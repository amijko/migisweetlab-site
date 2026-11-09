# Local Safe — Privacy policy

Effective date: 9 November 2026

Local Safe works without a network. Your data stays on your device.

## Data collection

Local Safe does not collect, transmit or sell your data. The app has no network calls and no analytics. The only third-party SDK is the Google Play feature delivery library, which the app uses only to request, check and remove the optional text recognition modules. On Android it does not declare the INTERNET permission.

## Storage

Your vault is one KDBX 4 file on your device. It is encrypted with your master password. You choose the file with the system file picker (Storage Access Framework on Android, Files on iOS). If you keep the file in Google Drive or iCloud, those services sync it outside the app under their own rules. Before saving, the app re-reads the file and merges changes made outside the app.

## Master password

The app never stores your master password. If you forget it, the app cannot recover your vault.

## Biometrics

If you turn on biometrics, the app stores the vault key (derived from your password) in encrypted form. On Android the encryption key is in the Android Keystore. It works only after strong biometric authentication and stops working when a new fingerprint is added. On iOS the key is in the Keychain. Access requires the current set of enrolled biometrics, the key stays on this device only, and it is stored only while a device passcode is set. The app cannot access your fingerprints or your face: the system performs the check.

## Permissions

On Android the app asks only for biometric authentication (USE_BIOMETRIC) and declares an autofill service. On iOS it uses only the Face ID usage description and a password AutoFill extension. The app has no access to your camera, contacts, location or network.

## Photos

You pick photos with the system photo picker (Android Photo Picker, iOS PHPicker). The app receives only the photos you select and has no access to your whole gallery. Text recognition on photos runs on your device, without a network. Your photos are never sent anywhere. On Android, Google Play downloads the recognition modules (ONNX Runtime and the PaddleOCR models) only when you turn on Fill from photo in Settings and choose the languages. The app itself does not connect to the network, and you can remove the modules in Settings at any time. On iOS the app uses Apple Vision.

## Autofill

Autofill fills your login and password only into the field you choose. It does not send them anywhere.

## Backups

The Android manifest allows system backups. The app keeps its settings, its list of recent vaults and its encrypted biometric key in a folder that is excluded from backups. The vault file stays where you chose to put it. The Android Keystore key does not leave the device.

## Deleting your data

To delete all your data, delete the vault file and uninstall the app. Uninstalling removes the app settings and the stored biometric key.

## Contact

Questions about this policy: migisweetlab@gmail.com
