<p align="center">
  <img src="banner.png" alt="Litematica Material Helper" width="420">
</p>

<h1 align="center">Litematica Material Helper</h1>

<p align="center">
  Turns Litematica material lists into a checklist you can actually work through.
</p>

---

## Features

- **All your lists in one place.** Every exported `materials_list_*.txt` shows up on the home page, newest first.
- **Readable amounts.** Instead of `3521` you see `2 shulkers, 1 stack and 1 item`, using the real stack size of each item (64, 16 or 1).
- **Item icons** for every block and item, downloaded once and cached.
- **Check things off** by clicking, or select rows and hit **Enter** to tick them and jump to the next one.
- **Remove stuff you don't need** with **Delete** (turn on "Show removed" to bring it back).
- **Sort and search** by name, amount or even "shulker".
- **Global shortcut** (Ctrl+Enter by default) so you can tick items off while you're still in Minecraft.
- **Progress is saved** per list, so you can close the app and pick up where you left off.

## Download

Grab the latest `.exe` from the [Releases](../../releases) page. No install needed, just run it.

## Running from source

You need Python 3.10 or newer.

```
pip install -r requirements.txt
python main.py
```

On first launch, go to **Settings** and pick the folder Litematica exports to. For a Modrinth install it's usually something like:

```
%AppData%\com.modrinth.theseus\profiles\<instance>\config\litematica
```

## Building the .exe

Run `build_exe.bat`. It installs PyInstaller and puts the exe in `dist/`.

## Where stuff gets saved

Everything goes into a `data/` folder next to the app (or next to the exe):

| Path | What |
| --- | --- |
| `data/config.json` | your settings |
| `data/progress/` | checked and removed items for each list |
| `data/icon_cache/` | downloaded icons |

The app never changes anything in your Litematica folder, it only reads from it.

## Icons

Icons come from [Owen1212055/mc-assets](https://github.com/Owen1212055/mc-assets). If an item isn't there, the app renders one itself from Minecraft's models via [misode/mcmeta](https://github.com/misode/mcmeta). If that fails too you get a placeholder, and you can retry in **Settings > Retry missing icons**.

## Limitations

- Only the `.txt` export from Litematica's material list screen is supported.
- Stack sizes come from a hardcoded list, so brand new items might show as stacking to 64.

## License

[MIT](LICENSE)
