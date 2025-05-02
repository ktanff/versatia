rolecontent = lambda message:{'role':message.role,'content':message.content[0].text.value}

def show_json(obj):
    from json import loads
    print(loads(obj.model_dump_json()))

def json_md(obj):
    from json import loads
    return ">```  \n"+loads(obj.model_dump_json())

def citation_quote_effect(q):
    from html import escape
    q = escape(q)
    q = "\n    ".join(line for line in q.splitlines() if line.strip())
    if any(c in "0123456789۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩&\n" for c in q[:13]):
        citation_quote = q[:13]
    else:
        citation_quote = f'<span class="text-blur3"> ...{q[:3]}</span><span class="text-blur2">{q[3:8]}</span><span class="text-blur1">{q[8:13]}</span>'
    citation_quote += q[13:-13]
    if any(c in "&\n" for c in q[-13:]):
        citation_quote += q[-13:] + "... "
    else:
        citation_quote += f'<span class="text-blur1">{q[-13:-8]}</span><span class="text-blur2">{q[-8:-3]}</span><span class="text-blur3">{q[-3:]}... </span>'
    return citation_quote

## Format the citations within a message response, and append a reference section.
def format_citations(msg_response,ref_section_title,details_open=False):
    mrt = msg_response.content[0].text
    v = mrt.value
    bdy= ''
    ftnts = []
    refidlist = {}
    ri = 0
    for a in mrt.annotations:
        if a.type=='file_citation':
            cite = a.text
            i = cite.index(':')
            hasquote = hasattr(a.file_citation,'quote') and a.file_citation.quote
            if hasquote:
                j = cite.index('†')
                hit = int(cite[i+1:j])
            else:
                hit = a.file_citation.filename
            if hit in refidlist:
                cntr, ref_id = refidlist[hit]
            else:
                cntr = len(ftnts)+1
                ref_id = f'ref{cite[1:i]}-{cntr}'
                if hasquote:
                    dtlsopen = ' open' if details_open else ''
                    ftnts.append(f'<details{dtlsopen}> <summary id="{ref_id}">{cntr}) {a.file_citation.filename}</summary> <blockquote><pre>{citation_quote_effect(a.file_citation.quote)}</pre></blockquote></details>')
                else:
                    ftnts.append(f'<li id="{ref_id}"> {a.file_citation.filename}</li>')
                refidlist[hit] = (cntr, ref_id)
            citef = f'<sup>【<a href="#{ref_id}" title="{a.file_citation.filename}">{cntr}</a>】</sup>'
            s = v[ri:a.start_index]
            if s:
                bdy += s + citef
            elif bdy[-len(citef):] != citef:
                 bdy += citef
            ri = a.end_index
    bdy += v[ri:]
    if ftnts:
        ftnts = '\n'.join(ftnts)
        return bdy+f'''<hr class="hr-ref-section">
<div class="ref-section-title">{ref_section_title}</div>
 <ol>
  {ftnts}
 </ol>'''
    else:
        return bdy

def flip_thread(t,citeuxmode=0):
    from ._openai_module01 import list_messages, is_closed_msg, resolve_filecitations, augment_quotes
    history = []
    for m in list_messages(t):
        if not is_closed_msg(m):
            if m.role=='user':
                history.append({'role':'user','content':m.content[0].text.value})
            else: # m.role=='assistant'
                if m.status!="completed":
                    m.content[0].text.value+=" /.. ..."
                if resolve_filecitations(m):
                    if citeuxmode!=1:
                        augment_quotes(m)
                    cntnt = format_citations(m,"مآخذ:",details_open=(citeuxmode==2))
                else:
                    cntnt = m.content[0].text.value
                history.append({'role':'assistant','content':cntnt})
    return history
