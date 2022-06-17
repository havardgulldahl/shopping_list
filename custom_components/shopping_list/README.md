[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/custom-components/hacs)
# Custom Shopping List with ~Bring~ Grosh integration.

A custom implementation of Home Assistant's Shopping List that synchronises with Grosh Shopping List (https://groshapp.com/). This overrides the core implementation of Shopping List and thus is accessible in Home Assistant from the sidebar or through the [Shopping List card](https://www.home-assistant.io/lovelace/shopping-list/)

## Usage

To use it, add the following to your configuration.yaml:

```yaml
shopping_list:
  grosh_username: 'username'
  grosh_password: 'password'
```

Full list of supported language isn't known, language should follow the `locale` format, such as `de-DE`, `fr-FR`, `ch-FR`, etc.
