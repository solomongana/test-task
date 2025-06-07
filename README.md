# Maubot Paystack Plugin

This repository contains a simple Maubot plugin that integrates Paystack payment processing.

## Environment variables

The plugin requires a couple of environment variables to be available when running:

* `PAYSTACK_SECRET` – Secret key from Paystack used for API requests.
* `PUBLIC_URL` – Publicly reachable URL for webhook callbacks and redirect links.

Make sure these variables are exported before starting the bot, for example:

```bash
export PAYSTACK_SECRET=sk_test_your_secret
export PUBLIC_URL=https://mybot.example.com
```

## Installing the plugin

1. Install `maubot` (and `mbc`), e.g. with `pip`:

```bash
pip install maubot
```

2. Build the plugin package:

```bash
mbc build
```

This will create a `*.mbplug` file that can be uploaded to Maubot.

3. Upload and enable the plugin in Maubot via the web UI or using `mbc`:

```bash
mbc auth https://your-maubot.example.com
mbc plugin upload paystack.mbplug
```

After uploading, enable the plugin for your bot instance in Maubot's admin interface.

## Database setup

The plugin uses Maubot's built-in database connection. Ensure the database is configured in your `maubot.yaml` configuration. If your Maubot setup requires running migrations, execute:

```bash
maubot manage db upgrade
```

Then start Maubot normally:

```bash
maubot serve -c maubot.yaml
```

With the environment variables configured and the plugin installed, Paystack events will be handled by the bot.
