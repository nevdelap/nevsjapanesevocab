#!/usr/bin/python
import shlex
import sys
from colors import color
from commands import *
from jamdict import Jamdict
from vocab import Vocab

# TODO - replace kanji

help = '''\n使い方:
  <漢字|仮名>\t\t検索
  l <漢字|仮名>\t\t辞書検索
  a <漢字>\t\t新漢字
  d <漢字>\t\t漢字削除
  a <漢字> <仮名>\t新仮名
  d <漢字> <仮名>\t仮名削除
  t <漢字>\t\tステータスを切り換える
  \t\t\t(%s 分かったか否か)
  u\t\t\t元に戻す
  r\t\t\t遣り直す
  s\t\t\t書き込む
  k\t\t\tデータ
  h\t\t\tこの使い方を表示する
  q\t\t\t終了
''' % color('✓', fg='green')


def replace_indices(
        vocab: Vocab,
        kanji_found: list[str],
        params: list[str]) -> list[str]:
    """ Given a set of search results, and command
    parameters that reference kanji and kana by index in
    those results, replace the indicies with the kanji and
    kana. """
    assert all(Vocab.valid_string(kanji) for kanji in kanji_found)
    assert all(vocab.contains(kanji) for kanji in kanji_found)
    assert all(len(p) > 0 for p in params)
    if len(params) > 1 and params[1].isnumeric():
        kanji_index = int(params[1]) - 1
        if kanji_index >= 0 and kanji_index < len(kanji_found):
            kanji = kanji_found[kanji_index]
            params[1] = kanji
            if len(params) > 2 and params[2].isnumeric():
                kana = vocab.get_kana(kanji)
                kana_index = int(params[2]) - 1
                if kana_index >= 0 and kana_index < len(kana):
                    params[2] = kana[kana_index]
    return params


def main() -> None:
    vocab_file = 'vocab.csv'
    try:
        print('読み込み中...')
        vocab = Vocab(vocab_file)
    except Exception as e:
        print(f'{vocab_file}が読み込みに失敗した。, ☹ {e}')
        sys.exit(1)

    command_stack = CommandStack()
    jam = Jamdict()

    print('ネフの日本語語彙リスト')
    print(help)
    previous_s = ''
    kanji_found = []
    while True:
        exact = False
        s = input('検索: ').strip()
        params = shlex.split(s)
        params = replace_indices(vocab, kanji_found, params)
        command = params[0] if len(params) > 0 else ''
        if len(params) == 0:
            s = previous_s
        elif s == 'q':
            break
        elif command in ['a', 'd']:
            if len(params) == 2:
                kanji = params[1]
                if command == 'a':
                    if vocab.contains(kanji):
                        print(f'{kanji}は既に有る')
                    else:
                        command_stack.do(AddCommand(vocab, kanji))
                    s = kanji
                    exact = True
                else:
                    if not vocab.contains(kanji):
                        print(f'{kanji}は見つからない。')
                    else:
                        command_stack.do(DeleteCommand(vocab, kanji))
                        print(f'{kanji}は削除した。')
                        kanji_found = []
                    continue
            elif len(params) == 3:
                kanji, kana = params[1:3]
                if not vocab.contains(kanji):
                    print(f'{kanji}は見つからない。')
                elif command == 'a':
                    if vocab.contains(kanji, kana):
                        print(f'{kanji}は{kana}が既に有る。')
                    else:
                        command_stack.do(AddKanaCommand(vocab, kanji, kana))
                else:
                    if not vocab.contains(kanji, kana):
                        print(f'{kanji}は{kana}が見つからない。')
                    else:
                        command_stack.do(DeleteKanaCommand(vocab, kanji, kana))
                        print(f'{kanji}は{kana}が削除した。')
                        kanji_found = []
                s = kanji
                exact = True
            else:
                print('使い方: %s <漢字> [仮名]' % command)
                continue
        elif command == 't':
            if len(params) == 2:
                kanji = params[1]
                if not vocab.contains(kanji):
                    print(f'{kanji}は見つからない。')
                    continue
                else:
                    command_stack.do(ToggleKnownCommand(vocab, kanji))
                    s = kanji
                    exact = True
            else:
                print('使い方: t <漢字>')
                continue
        elif s == 'u':
            if command_stack.undoable():
                print(command_stack.undo())
                kanji_found = []
            else:
                print('元に戻すものがない。')
            continue
        elif s == 'r':
            if command_stack.redoable():
                print(command_stack.redo())
                kanji_found = []
            else:
                print('遣り直しものがない。')
            continue
        elif s == 's':
            try:
                print('書き込み中...')
                vocab.save()
            except Exception as e:
                print(f'{vocab_file}が書き込みに失敗した。☹ {e}')
                sys.exit(1)
            continue
        elif s == 'k':
            print('データ:\n  分かった: %d\n  学んでいる %d\n  合計: %d\n' %
                  vocab.get_stats())
            continue
        elif command == 'l':
            if len(params) == 2:
                result = jam.lookup(params[1])
                for entry in result.entries:
                    print('  ' + entry.text(True))
                continue
            else:
                print('使い方: l <漢字|仮名>')
                continue
        elif s == 'h':
            print(help)
            continue
        elif len(params) > 1:
            print('使い方: h 使い方を表示する')
            continue
        elif s != '':
            previous_s = s
        if s == '':
            continue
        kanji_found = vocab.search(s, exact)
        if len(kanji_found) > 0:
            print('見つかった: (%d)' % len(kanji_found))
            for kanji_index, kanji in enumerate(kanji_found):
                out = '%s %s %s ' % (color(
                    '%4d' % (kanji_index + 1),
                    fg='grey'),
                    color(
                    vocab.get_list_name(kanji),
                    fg='grey'),
                    kanji)
                known = '✓' if vocab.get_known(kanji) else ''
                kana_list = vocab.get_kana(kanji)
                out += color(
                    ' '.join(
                        [
                            f'{color(str(kana_index + 1), fg="grey")} {kana}' for kana_index,
                            kana in enumerate(kana_list)]),
                    fg='grey') + ' '
                out += color(known, fg='green')
                print('  ' + out)
        else:
            previous_s = s = ''
            print('何も見つからない。')

    print('データ:\n  分かった: %d\n  学んでいる %d\n  合計: %d\n' % vocab.get_stats())

    try:
        print('書き込み中...')
        vocab.save()
    except Exception as e:
        print(f'{vocab_file}が書き込みに失敗した。☹ {e}')
        sys.exit(1)

    sys.exit(0)


if __name__ == '__main__':
    main()
