# Discord Export CLI Utility (discordexport)

`discordexport` is a Python command-line utility that allows you to export messages from Discord channels, including both servers and direct messages. It provides a flexible set of options for exporting messages, and it can also automatically retrieve the authentication token from Firefox and Chromium cookies. Additionally, it offers an interactive prompt to list servers and channels for ease of use.

## Usage

### Basic Usage

To export messages, you need to specify the authentication token, server ID (optional for direct messages), channel ID, and output file path. The basic command structure is as follows:

```bash
discordexport --token <Authentication Token> --server-id <Server ID> --channel-id <Channel ID> --output <Output File>
```

- `--token`: The Discord authentication token. You can either provide it directly or use the automatic retrieval from cookies feature.
- `--server-id`: The ID of the Discord server. Leave this empty for direct messages.
- `--channel-id`: The ID of the Discord channel.
- `--output`: The path to the output file where the exported messages will be saved.

### Optional Arguments

- `--log`: Specify the log level for debugging and error messages. Options are: `debug`, `info`, `warn`, `error`, and `quiet`. Default is `info`.
- `--help`: Show the help message and exit.

### Automatic Token Retrieval

To automatically retrieve the authentication token from Firefox and Chromium cookies, simply omit the `--token` option. `discordexport` will attempt to find the token in your browser's cookies.

### Interactive Server and Channel Selection

If you don't know the server and channel IDs, you can run `discordexport` without specifying them. It will interactively prompt you to select the server and channel from a list.

```bash
discordexport --output <Output File>
```

## Examples

1. Export messages from a Discord server channel with a provided token:

```bash
discordexport --token <Authentication Token> --server-id <Server ID> --channel-id <Channel ID> --output messages.txt
```

2. Export messages from a direct message conversation with automatic token retrieval:

```bash
discordexport --output messages.txt
```

3. List available servers and channels interactively and then export messages:

```bash
discordexport --output messages.txt
```

## Logging

`discordexport` provides detailed logging to help you understand what it's doing and to troubleshoot any issues. You can control the log level using the `--log` option.

## Help

If you need assistance or have questions, use the `--help` option to display the help message.

```bash
discordexport --help
```

## Note

This utility is intended for personal use and adheres to Discord's terms of service. Be responsible and respectful when exporting messages, and ensure you have the necessary permissions to access the channels you want to export.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
