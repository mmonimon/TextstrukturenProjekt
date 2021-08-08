#!/usr/bin/env python
# coding: utf-8

# ### TODO
# - Hover verbessern (oben wird abgeschnitten, bessere eigenschaften anzeigen)
# - Page title anpassen

# In[351]:


import json, re, string


# In[389]:


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
  width: 120px;
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


# In[390]:


with open('data/dimlex.json') as j:
    dimlex_raw = json.load(j)


# In[423]:


## Creates dictionary that saves necessary information about connector
conn_dict = {}
for entry in dimlex_raw['entry']:
    word_regex = '(^| )(' + entry['word']
    if '...' in word_regex:
        word_regex = re.sub('\s?\.{3}\s?',' [^.?!]+ ',word_regex)
    for orth in entry['orths']['orth']:
        orth_variant = ' '.join(part['t'] for part in orth['part'])
        word_regex += '|' + orth_variant
        # print(orth_variant)
    word_regex += ')( |\.|\?|!|$)'
    if word_regex not in conn_dict:
        # print(word_regex)
        conn_dict[word_regex] = {'non_conn': entry['ambiguity']['non_conn']}
        # print(entry['ambiguity'], entry['non_conn_reading'])
        conn_dict[word_regex]['example'] = ''
        if 'example' in entry['non_conn_reading']:
            # if entry['non_conn_reading']['example'] != [[]]:
            
            for sub_entry in entry['non_conn_reading']['example']:
                if 't' in sub_entry and 'type' in sub_entry:
                    conn_dict[word_regex]['example'] += '{}: {}\n'.format(sub_entry.get('type'),sub_entry['t'])
                elif 't' in sub_entry:
                    conn_dict[word_regex]['example'] += '{}\n'.format(sub_entry['t'])
                    
            
    else: 
        print(dimlex_raw['entry'].index(entry), word_regex, entry['ambiguity']['non_conn'], 'already in dict')


# In[424]:


html_string='<!DOCTYPE html>\n<html>\n<head>\n<title>ConnReco</title>\n</head>\n<body><div class="container">\n<p>\n<h1>' # start of paragraph
header_closed = False
with open("data/coronaimpfung.txt") as txt: # https://www.dw.com/de/coronaimpfung-die-m%C3%A4r-von-der-unfruchtbarkeit/a-58733733
    for line in txt:
        if line.strip() == '': 
            html_string+="</p>\n<p>"
            if header_closed == False:
                html_string += "</h1>"
                header_closed = True
            
        html_line = line
        for conn_reg in conn_dict:
            # print(conn_reg, conn_dict[conn_reg])
            ttt = conn_dict[conn_reg]['example']
            rr = '\g<2><span class="tooltiptext">{ttt}</span></span> '.format(ttt=ttt)
            if conn_dict[conn_reg]['non_conn']['t'] == 0:
                rr = ' <span class="tooltip green">' + rr
            else: 
                rr = ' <span class="tooltip red">' + rr
            html_line = re.sub(conn_reg, r'{}'.format(rr), html_line)
        html_string+=html_line
        html_string+="\n"
html_string+="</div></body>\n</html>"


# In[425]:


html = open('html/output.html', mode='w', encoding='utf8') 
html.write(html_string)
## add style: https://www.w3schools.com/css/css_tooltip.asp
html.write(CSS)
html.close()


# In[278]:


html_string
conn_dict


# In[250]:


s = "hält sich aber hartnäckig aber."


# In[251]:


re.sub('(^| )(aber|aber|Aber)( |\.|\?|!|$)', r' <font color=\"green\">\g<2></font> ', s)


# In[224]:


re.search('[\s^](aber|aber|Aber)[\\s\\.?!\\$]', s)


# In[ ]:




