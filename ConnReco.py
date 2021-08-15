#!/usr/bin/env python
# coding: utf-8

# # V5: Konnektoren erkennen.
# Dieses Programm liest das deutsche Konnektorenlexikon DimLex als JSON ein (heruntergeladen von https://github.com/discourse-lab/Connective-Lex.info/blob/master/Web%20app/xml/dimlex.json, gefunden auf connective-lex.info) ein und merkt sich den Konnektor-string als Regular Expression, sowie die Information, ob das Wort auch eine Nicht-Konnektor Lesart hat. 
# 
# Dann kann ein Text als txt-Datei eingelesen werden, welcher in eine html-Datei transformiert wird, die denselben Text enthält, in dem aber alle Wörter, die mit einem Konnektor-string übereinstimmen, farblich markiert sind: 
# - Grün = dieses Wort ist in jedem Fall ein Konnektor.
# - Rot = dieses Wort kann ein Konnektor sein, muss aber nicht. 

# ### 1. Import von benötigten Libraries
# Die Implementierung basiert vorwiegend auf Regular Expressions, daher wird die Bibliothek "re" benötigt. Darüber hinaus brauchen wir "json" um die konvertierte DimLex JSON-Datei dimlex.json einfach parsen zu können.

import sys, argparse, json, re

## Style-elemente (CSS) definieren
# tooltip nach: https://www.w3schools.com/css/css_tooltip.asp
CSS = """<style>\n
* {
  font-family: monospace;
}

.red {
  color: red;
}

.green {
  color: green;
}

.container {
  margin: 50px;
}

.tooltip {
  position: relative;
  display: inline-block;
  border-bottom: 1px dotted black;
}

.tooltip .tooltiptext {
  visibility: hidden;
  width: 120px;
  background-color: black;
  color: #fff;
  text-align: center;
  border-radius: 6px;
  padding: 5px 0;
  bottom: 100%;
  left: 50%;
  margin-left: -60px; /* Use half of the width (120/2 = 60), to center the tooltip */
  /* Position the tooltip */
  position: absolute;
  z-index: 1;
}

.tooltip:hover .tooltiptext {
  visibility: visible;
}

.tooltip .tooltiptext::after {
  content: " ";
  position: absolute;
  top: 100%; /* At the bottom of the tooltip */
  left: 50%;
  margin-left: -5px;
  border-width: 5px;
  border-style: solid;
  border-color: black transparent transparent transparent;
}

</style>"""



def parse_dimlex(dimlex):
  # ### 2. Einlesen der DimLex JSON-Datei
  # Da JSON in Python einfacher als XML einzulesen ist und ich persönlich mehr Erfahrung damit habe, habe ich mich dafür entschieden, die konvertierte dimlex.json aus dem Git Repository für connective-lex.info herunterzuladen und diese einzulesen.
  with open(dimlex) as j:
    try:
      dimlex_raw = json.load(j)
    except:
      print("[ERROR] Error while reading JSON file. Please make sure the file is not empty and contains JSON syntax.")
      exit(1)

  # #### 2.1 Daten in geeigneter Datenstruktur speichern
  # Es wird ein Dictionary mit den eingelesenen, benötigten Daten erstellt. Da ich in diesem Programm mit Regular expressions arbeite, habe ich die eingelesenen Konnektoren in Regex umgewandelt (z.B. `'(^| )([zZ]war)( |\\.|,|\\?|!|$)'`) - diese sind die Keys des Dictionaries.
  # Die Values geben Informationen über die Eigenschaft "auf jeden Fall ein Konnektor sein oder nicht" und wurde aus dem DimLex adaptiert (z.B. `{'t': 0}`).

  # Konnektor dict initialisieren
  conn_dict = {}
  # durch alle Einträge im DimLex iterieren
  for entry in dimlex_raw['entry']:
      # Regular expression für Satzanfang (Großbuchstabe) und Satzmitte (Kleinbuchstabe) erstellen 
      new_conn = '[' + entry['word'][0].lower()+entry['word'][0].upper() + ']' + entry['word'][1:]
      # Drei Punkte in der Mitte eines Konnektorstrings werden mit einer Placeholder Regex ersetzt
      # Diese sollte alles matchen, was in der Mitte steht außer Satzzeichen
      if '...' in new_conn:
          new_conn = re.sub('\s?\.{3}\s?', ' [^.?!]+ ', new_conn)
      # Leerzeichen um das Wort/die Wortgruppe entfernen 
      new_conn = new_conn.strip()
      # In den Orths nachschauen, ob es noch andere Schreibweisen gibt, die wir noch nicht in der Regex haben
      for orth in entry['orths']['orth']:
          # Fügt Einzelteile einer Variante zusammen
          orth_variant = ' '.join(part['t'] for part in orth['part'])
          # Überprüfen, ob die Variante bereits von der Regex abgedeckt wird
          if not re.search(new_conn, orth_variant):
              # Wenn nicht, machen wir das gleiche wie oben um das Wort am Satzanfang/-mitte abzufangen
              orth_variant = '[' + orth_variant[0].lower()+orth_variant[0].upper() + ']' + orth_variant[1:]
              # Und dann wird es mit einem "oder" an die Regex angehangen
              new_conn += '|' + orth_variant
      # Start- und Endkontext der Regex definieren und bisherige Konnektorregex einfügen
      conn_regex = '(^| )(' + new_conn + ')( |\.|,|\?|!|$)'
      # Wir überprüfen, ob die Regex schon im Dict ist (unwahrscheinlich, aber sicher ist sicher)
      if conn_regex not in conn_dict:
          # Erstelle Eintrag mit Ambiguitätenwert für "non_conn"
          conn_dict[conn_regex] = {'non_conn': entry['ambiguity']['non_conn']}
          # Erstelle leeres Beispiel, da nicht alle Konnektoren ein Beispiel für Nicht-Konnektor enthalten
          conn_dict[conn_regex]['example'] = ''
          # Falls es aber einen Beispielsatz gibt, füge ihn an dieser Stelle ein
          if 'example' in entry['non_conn_reading']:
              for sub_entry in entry['non_conn_reading']['example']:
                  # Inklusive Tag, falls es eines gibt
                  if 't' in sub_entry and 'type' in sub_entry:
                      conn_dict[conn_regex]['example'] += '{}: {}\n'.format(sub_entry.get('type'),sub_entry['t'])
                  # Wenn es keins gibt, nur den Beispielsatz hinzufügen
                  elif 't' in sub_entry:
                      conn_dict[conn_regex]['example'] += '{}\n'.format(sub_entry['t'])
      # gibt Zeile und Regex aus, falls schon im Dict vorhanden
      else: 
          print(dimlex_raw['entry'].index(entry), conn_regex, entry['ambiguity']['non_conn'], 'already in dict')
  return conn_dict

# ### 3. Text einlesen und HTML String erstellen
# Der eingelesene Text (txt-Datei mit einer Überschrift in der ersten Zeile) wird Zeile für Zeile eingelesen und in einen HTML-String umgewandelt. Diese enthält derzeit die eingefärbten Konnektoren und einen Hovertext mit den "non_conn" Informationen aus dem DimLex Lexikon.
# 
# Note: Ich wollte urpsrünglich noch Beispielsätze mit in den Hovertext einbauen, diese machten aber den Hovertext zu lang und nicht gut überschaubar. Für ein anderes Projekt könnte man aber auch andere Informationen in den Hovertext einbauen, um wie auf der connective-lex.info page schnell zu anderen Infos wie semantische Rollen oder syntaktische Stellung zu erhalten.
def convert_to_html(conn_dict, input_txt):
  # Beginn des HTML-Strings, der später in die HTML-Datei geschrieben werden soll
  html_string = """
  <!DOCTYPE html>
  <html>
  <head>
  <title>V5: Konnektoren erkennen</title>
  {}
  </head>
  <body>
  <div class="container">
  <h1>
  """.format(CSS)
  # Wir starten mit einen geöffneten Header (siehe vorherige Zeile) und setzen einen Boolean, weil dieser noch nicht geschlossen ist
  header_closed = False
  # Öffne die eingelesene Textdatei
  print("[INFO] Reading input text file {}".format(input_txt))
  with open(input_txt) as txt: 
      # Lese Zeile für Zeile ein und bearbeite diese
      for line in txt:
          # Wenn die erste Leerzeile (ohne Umbruch/Leerzeichen) kommt (deshalb muss Überschrift in der ersten Zeile stehen)
          if line.strip() == '': 
              # ... und der Heade noch nicht geschlossen ist
              if header_closed == False:
                  # schließe den header und beginne neuen Absatz
                  html_string += "</h1>\n<p>"
                  # setze Bool auf True
                  header_closed = True
              # Wenn wir schon eine Überschrift haben, fang nur einen neuen Absatz an
              else:
                  html_string+="</p>\n<p>"
          
          # Jetzt zum eigentlichen Bearbeiten des Textes
          html_line = line
          # Das Konnektorendict wird nach Keylänge (=Länge des Strings) sortiert, weil längere Konnektorenstrings
          # Priorität haben sollen z.B. "sowohl ... als auch" hat Priorität über "als" oder "auch"
          # Das ist wichtig, weil sonst nur die kürzeren Strings markiert werden könnten
          for conn_reg in sorted(conn_dict, key=len, reverse=True):
              # Wir schauen erst einmal, ob die Regex für unsere Zeile relevant ist
              if re.search(conn_reg, html_line):
                  # Hier nehmen wir den Text für den Tooltip heraus (derzeit nur Infos zur Frequenz des Auftretens als Non-Connector)
                  ttt = conn_dict[conn_reg]['non_conn']
                  # Tooltiptext in den String einfügen (nur für Konnektor)
                  html_substring = '\g<2><span class="tooltiptext">{ttt}</span></span>\g<3>'.format(ttt=ttt)
                  # Überprüfe, ob der Konnektor auch ein Nicht-Konnektor sein kann
                  if conn_dict[conn_reg]['non_conn']['t'] == 0:
                      # Wenn nicht --> färbe grün
                      html_substring = '\g<1><span class="tooltip green">' + html_substring
                  else: 
                      # wenn ja --> färbe rot
                      html_substring = '\g<1><span class="tooltip red">' + html_substring
                  # Ersetze alten substring mithilfe der Konnektorregex
                  html_line = re.sub(conn_reg, r'{}'.format(html_substring), html_line)
          # füge alles zum html string hinzu
          html_string+=html_line
          html_string+="\n"
  # schließe html syntax
  html_string+="</div></body>\n</html>"
  return html_string

# Main function
def main(main_args):
    parser = argparse.ArgumentParser(
        description = """This program reads and parses the DimLex lexicon as a JSON file and converts an input txt file into a html file, containing the same text, 
        but marking connector strings in green (there is no doubt that this is a connector) or red (this might be a connector, but can be something else too).""")
    parser.add_argument(
        '-d', '--dimlex',
        help = """Full path to the DimLex file. Default is data/dimlex.json""",
        metavar = 'DIMLEX',
        default = 'data/dimlex.json')
    parser.add_argument(
        '-i', '--input_txt',
        help = """Full or relative path to txt input file. Default is a sample file in data/ this repository""",
        metavar = 'INPUT_TXT',
        default = 'data/coronaimpfung.txt')
    parser.add_argument(
        '-o', '--output_html',
        help = """Full or relative path to html output file. Default is the html/ folder in this repository""",
        metavar = 'OUTPUT_HTML',
        default = 'html/coronaimpfung.html')
    args = parser.parse_args(main_args)

    dimlex = args.dimlex
    input_txt = args.input_txt
    output_html = args.output_html

    # ### 2. Einlesen der DimLex JSON-Datei
    
    if not dimlex.endswith('.json'): 
      print("[ERROR] The DimLex file format is not supported. Please use a DimLex JSON file instead.")
      exit(1)
    print("[INFO] Parsing DimLex file {}".format(dimlex))
    conn_dict = parse_dimlex(dimlex)

    # ### 3. Text einlesen und HTML String erstellen
    html_string = convert_to_html(conn_dict, input_txt)

    # ### 4. HTML-Datei schreiben
    # Die Output-Datei wird nach html/ geschrieben und enthält den zuvor erhaltenen HTML-String.
    print("[INFO] Writing output file to {}".format(output_html))
    with open(output_html, mode='w', encoding='utf8') as html:
        html.write(html_string)

# Execution  
if __name__ == '__main__':
    main(sys.argv[1:])