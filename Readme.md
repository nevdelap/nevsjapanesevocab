# Nev's Japanese Vocab

## What Is This?

This is a Python terminal application that I use on my phone and tablet to manage Japanese vocabulary that I am learning. I've used various Android apps but I wanted something that does exactly what I require, and I have zero interest in App development. ;)

It is Python 3 with typing, tests, full undo/redo, and uses [Pykakasi](https://github.com/miurahr/pykakasi) for kanji to kana conversion, and [Jamdict](https://github.com/neocl/jamdict) for dictionary lookups. Its feature set is just exactly what I personally need, I need even fewer Android apps.

**NOTE: I don't expect anyone to use this, you have to be a terminal nut for a start. This repo and these instructions are for my own use.**

## Vocabulary

The original list is Kanshudo's top 5000 words by usefulness, stripped of hiragana only words, and now augmented with my own words from books, movies, and TV programs.

Reference: https://www.kanshudo.com/collections/vocab_usefulness2021

## Setup on Linux

1. Standard dev environment, VS Code, all my extensions, Python 3, `entr`, `gettext`, and `sed`.
1. The Python packages and tools listed below.
1. Added VS Code's settings: `"python.linting.banditArgs": ["--ini=${workspaceFolder}/.bandit"],` It has a `.vscode/launch.json` and `.bandit` for VSCode.

## Setup On Android

1. Install [Termux](https://f-droid.org/en/packages/com.termux/) from F-Droid.
1. Install [Termux Widget](https://f-droid.org/en/packages/com.termux.widget/) from F-Droid.
1. Install [Code Editor](https://play.google.com/store/apps/details?id=com.rhmsoft.code).
1. `pkg update`
1. `pkg install entr git python`
1. `termux-setup-storage`
1. `ssh-keygen`
1. `cat .ssh/id_rsa.pub # Copy it into GitHub.`
1. `mkdir -p ~/.shortcuts`
1. `chmod 700 ~/.shortcuts`
1. `cd ~/storage/shared/`
1. `git clone git@github.com:nevdelap/nevsjapanesevocab.git`
1. `cd nevsjapanesevocab`
1. `bash install_termux`
1. `pip install --upgrade wheel`
1. `pip install --upgrade ansicolors autopep8 jamdict jamdict-data mypy pykakasi pytest readline`
1. Create a Termux Widget to run `~/.shortcuts/vocab`

## Usage

You need to know how to use a Japanese keyboard, on a phone, tablet or computer, or use an IME for a computer, otherwise the usage is there, in Japanese.

If anyone want's to tell me better translations than I have in the program's UI, I'd sure appreciate it. :)

The usage doesn't describe some features of indexing the search results and referring to the last search as 0, because describing it is beyond my Japanese. They are for driving it fast on the Android device where you don't have a full keyboard. :P

<img src="screenshots/screenshot.jpg" width="480">
<img src="screenshots/screenshot2.jpg" width="480">
<img src="screenshots/screenshot3.jpg" width="960">

