import pytest
from test_helpers import strip_ansi_terminal_escapes

from localisation import set_locale
from operations import format_help

# Content is simply copied out of the terminal into the test for
# regression testing and proof reading.


@pytest.mark.parametrize('locale, expected_help',
                         [
                             ('ja', '''
使い方:
     漢字｜仮名　　　　　検索
  l  日本語｜英語　　　　和英辞書で検索する。
  a  漢字　　　　　　　　新漢字
  d  漢字　　　　　　　　漢字削除
  c  漢字　新漢字　　　　漢字変更
  ak 漢字　仮名　　　　　新仮名
  dk 漢字　仮名　　　　　仮名削除
  ck 漢字　仮名　新仮名　仮名変更
  t  漢字　　　　　　　　分かったか✓否かを切り換える。
  u  　　　　　　　　　　元に戻す。
  r  　　　　　　　　　　遣り直す。
  s  　　　　　　　　　　書き込む。
  i  　　　　　　　　　　データ
  en 　　　　　　　　　　English
  es 　　　　　　　　　　español
  fr 　　　　　　　　　　français
  ja 　　　　　　　　　　日本語
  h  　　　　　　　　　　この使い方を表示する。
  q  　　　　　　　　　　終了
'''),
                             ('en', '''
Help:
     kanji|kana          Search.
  l  Japanese|English    Search the Japanese/English dictionary.
  a  kanji               Add a new kanji.
  d  kanji               Delete a kanji.
  c  kanji new-kanji     Change a kanji.
  ak kanji kana          Add a new kana to a kanji.
  dk kanji kana          Delete a kana from a kanji.
  ck kanji kana new-kana Change a kana for a kanji.
  t  kanji               Toggle known ✓ status.
  u                      Undo.
  r                      Redo.
  s                      Save.
  i                      Show info, known & learning.
  en                     English
  es                     español
  fr                     français
  ja                     日本語
  h                      Show this help.
  q                      Quit.
'''),
                             ('es', '''
Uso:
     kanji|kana            Buscar.
  l  japonés|inglés        Buscar en el diccionario japonés/inglés.
  a  kanji                 Añadir un kanji.
  d  kanji                 Borrar un kanji.
  c  kanji kanji-nuevo     Cambiar un kanji.
  ak kanji kana            Añadir un kana.
  dk kanji kana            Borrar un kana.
  ck kanji kana kana-nuevo Cambiar un kana.
  t  kanji                 Cambiar el estado conocido ✓.
  u                        Deshacer.
  r                        Rehacer.
  s                        Guardar.
  i                        Mostrar la información, conocidos y se apprenden.
  en                       English
  es                       español
  fr                       français
  ja                       日本語
  h                        Mostrar esta ayuda.
  q                        Salir.
'''),
                             ('fr', '''
L'utilisation:
     kanji|kana              Chercher.
  l  japonais|anglais        Rechercher dans le dictionnaire japonais/anglais.
  a  kanji                   Ajouter un kanji.
  d  kanji                   Supprimer un kanji.
  c  kanji kanji-nouveau     Changer un kanji.
  ak kanji kana              Ajouter un nouveau kana.
  dk kanji kana              Supprimer un kana.
  ck kanji kana kana-nouveau Changer un kana.
  t  kanji                   Basculer l'état connu ✓.
  u                          Défaire.
  r                          Refaire.
  s                          Sauvegarder.
  i                          Afficher des informations, connu et pour apprendre.
  en                         English
  es                         español
  fr                         français
  ja                         日本語
  h                          Afficher cet aide.
  q                          Quitter.
'''),
                         ]
                         )
def test_help(locale: str, expected_help: str) -> None:
    set_locale(locale)
    assert strip_ansi_terminal_escapes(format_help()) == expected_help
