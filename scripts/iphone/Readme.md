# iPhone

I've been using iPhone 16 since Sep 2024 - which is one of my sources of data.

## Exporting

I tried using iMazing - seemed to work, but don't want to be on a subscription based application.

Used Apple Devices application on Windows to take a backup of the

## Decrypting

Used [`iphone_backup_decrypt`](https://github.com/KnugiHK/iphone_backup_decrypt/) to decrypt & extract files from the backup folder:

```python
from iphone_backup_decrypt import EncryptedBackup, RelativePath, MatchFiles

passphrase = "12345"
backup_path = "C:\\users\\duffe\\Apple\\MobileSync\\Backup\\[device-id]"

backup = EncryptedBackup(backup_directory=backup_path, passphrase=passphrase)

backup.extract_file(relative_path=RelativePath.ADDRESS_BOOK,
                    output_filename="./output/address_book.sqlite")

backup.extract_file(relative_path=RelativePath.CALL_HISTORY,
                    output_filename="./output/call_history.sqlite")

backup.extract_file(relative_path=RelativePath.TEXT_MESSAGES,
                    output_filename="./output/text_messages.sqlite")

backup.extract_file(relative_path=RelativePath.HEALTH,
                    output_filename="./output/health.sqlite")

backup.extract_file(relative_path=RelativePath.HEALTH_SECURE,
                    output_filename="./output/health_secure.sqlite")

backup.extract_file(relative_path=RelativePath.WHATSAPP_MESSAGES,
                    output_filename="./output/whatsapp.sqlite")
```

## WhatsApp

Exporting WhatsApp messages was done by: https://github.com/KnugiHK/WhatsApp-Chat-Exporter

```bash
wtsexporter -i -b "C:\\Users\\[Username]\\Apple\\MobileSync\\Backup\\[device id]"
```