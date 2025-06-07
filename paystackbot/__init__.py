from maubot import Plugin, MessageEvent, event
from maubot.handlers import command, event_match
from mautrix.types import EventType, MessageType, Format, TextMessageEventContent
from mautrix.util.async_db import Database
from aiohttp import web
import os
import json


class PaystackBot(Plugin):
    async def start(self) -> None:
        self.paystack_secret = os.environ.get("PAYSTACK_SECRET")
        self.public_url = os.environ.get("PUBLIC_URL", "")
        if not self.paystack_secret:
            self.log.warning("PAYSTACK_SECRET not configured")
        self.webapp.router.add_post("/paystack", self.paystack_webhook)
        self.webapp.router.add_get("/delivery", self.deliver_confirm)
        self.webapp.router.add_get("/pay", self.pay_page)
        await super().start()

    async def paystack_webhook(self, request: web.Request) -> web.Response:
        body = await request.json()
        ref = body.get("data", {}).get("reference")
        if not ref:
            return web.Response(status=400)
        quote = await self.db.fetchrow("SELECT * FROM quotes WHERE reference = $1", ref)
        if not quote:
            return web.Response(status=404)
        await self.db.execute(
            "UPDATE quotes SET status='paid' WHERE reference=$1", ref
        )
        self.loop.create_task(self.after_payment(quote))
        return web.Response(text="ok")

    async def after_payment(self, quote: dict) -> None:
        buyer = quote["buyer"]
        await self.client.send_text(buyer, "Payment received! We'll confirm delivery in 24h.")
        await self.db.execute(
            "UPDATE quotes SET remind_time = now() + interval '24 hours' WHERE reference=$1",
            quote["reference"],
        )
        self.loop.call_later(24*3600, lambda: self.loop.create_task(self.delivery_reminder(buyer, quote)))

    async def delivery_reminder(self, buyer: str, quote: dict) -> None:
        msg = (
            f"Did you receive '{quote['item']}'?"
            f" [✅ Yes]({self.public_url}/delivery?ref={quote['reference']}&ok=1) "
            f"[🚫 Problem]({self.public_url}/delivery?ref={quote['reference']}&ok=0)"
        )
        content = TextMessageEventContent(msgtype=MessageType.TEXT, format=Format.HTML, formatted_body=msg)
        await self.client.send_message(buyer, content)

    async def deliver_confirm(self, request: web.Request) -> web.Response:
        ref = request.query.get("ref")
        ok = request.query.get("ok") == "1"
        quote = await self.db.fetchrow("SELECT * FROM quotes WHERE reference=$1", ref)
        if not quote:
            return web.Response(status=404)
        if ok:
            await self.transfer_to_seller(quote)
            await self.client.send_text(quote["buyer"], "Thanks for confirming!")
        else:
            await self.client.send_text(quote["buyer"], "We'll look into the issue.")
        return web.Response(text="ok")

    async def transfer_to_seller(self, quote: dict) -> None:
        # call Paystack transfer API
        pass

    @event_match(EventType.ROOM_MESSAGE, msgtype=MessageType.TEXT)
    async def on_message(self, evt: MessageEvent) -> None:
        body = evt.content.body.strip().lower()
        if body == "register bank":
            await self.start_register_bank(evt)
        elif body == "send quote":
            await self.start_quote(evt)

    async def start_register_bank(self, evt: MessageEvent) -> None:
        await evt.respond("Please enter account number:")
        resp = await self.wait_for_next_message(evt.sender)
        account = resp.content.body.strip()
        await evt.respond("Enter bank code:")
        resp2 = await self.wait_for_next_message(evt.sender)
        bank = resp2.content.body.strip()
        await self.db.execute(
            "INSERT INTO banks (user_id, account, bank) VALUES ($1, $2, $3)",
            evt.sender, account, bank
        )
        await evt.respond("Bank registered.")

    async def start_quote(self, evt: MessageEvent) -> None:
        await evt.respond("Item?")
        item = (await self.wait_for_next_message(evt.sender)).content.body.strip()
        await evt.respond("Quantity?")
        qty = (await self.wait_for_next_message(evt.sender)).content.body.strip()
        await evt.respond("Price?")
        price = (await self.wait_for_next_message(evt.sender)).content.body.strip()
        ref = "ref-" + os.urandom(4).hex()
        await self.db.execute(
            "INSERT INTO quotes (reference, item, qty, price, buyer, seller, status)"
            " VALUES ($1, $2, $3, $4, $5, $6, 'pending')",
            ref, item, qty, price, evt.room_id, evt.sender
        )
        pay_link = f"{self.public_url}/pay?ref={ref}"
        msg = f"Please pay: [💳 Pay now]({pay_link}) [✖ Decline]({pay_link}&decline=1)"
        content = TextMessageEventContent(msgtype=MessageType.TEXT, format=Format.HTML, formatted_body=msg)
        await self.client.send_message(evt.room_id, content)

    async def pay_page(self, request: web.Request) -> web.Response:
        ref = request.query.get("ref")
        quote = await self.db.fetchrow("SELECT * FROM quotes WHERE reference=$1", ref)
        if not quote:
            return web.Response(status=404)
        if request.query.get("decline"):
            await self.db.execute("UPDATE quotes SET status='declined' WHERE reference=$1", ref)
            await self.client.send_text(quote["seller"], "Buyer declined the quote.")
            return web.Response(text="declined")
        checkout = await self.create_checkout(quote)
        raise web.HTTPFound(checkout)

    async def create_checkout(self, quote: dict) -> str:
        headers = {"Authorization": f"Bearer {self.paystack_secret}", "Content-Type": "application/json"}
        payload = {
            "amount": int(float(quote["price"]) * 100),
            "email": quote["buyer"],
            "reference": quote["reference"],
        }
        async with self.http.post("https://api.paystack.co/transaction/initialize", json=payload, headers=headers) as resp:
            data = await resp.json()
        return data["data"]["authorization_url"]

    async def wait_for_next_message(self, user_id: str) -> MessageEvent:
        fut = self.loop.create_future()

        @event_match(EventType.ROOM_MESSAGE, msgtype=MessageType.TEXT, sender=user_id)
        async def waiter(evt: MessageEvent) -> None:
            if not fut.done():
                fut.set_result(evt)
        self.add_event_handler(waiter)
        res = await fut
        self.remove_event_handler(waiter)
        return res
