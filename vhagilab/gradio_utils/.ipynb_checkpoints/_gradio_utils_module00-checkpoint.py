import gradio as __gr

_default_tagline = ''
def set_default_tagline(TAGLINE:str,**kwargs):
    global _default_tagline
    _default_tagline = '<div class="footer"><p><small>'+TAGLINE+'</small></p></div><footer>'

def add_tagline(tl=_default_tagline):
    if tl:
        tl='<div class="footer"><p><small>'+tl+'</small></p></div><footer>'
    else:
        tl=_default_tagline
    __gr.HTML(tl)

def trimnondigit(s):
    i=0
    for a in s:
        if not a.isdigit():
            return s[:i]
        i+=1
    return __gr.skip()

def force_digitonly(textbox:__gr.Textbox):
    __gr.on(textbox.input,trimnondigit,
            inputs=textbox,
            outputs=textbox,
            show_progress='hidden',trigger_mode='once')

def _theme(theme_name:str,**kwargs) -> __gr.themes.ThemeClass:
    return getattr(__gr.themes, theme_name, __gr.themes.Default)(**kwargs)

def _set_a_default_font(fnt,fonts,fmap):
    if fnt:
        if fnt[0]=='*':
            gfont=True
            fnt=fnt[1:]
        if fnt in fonts:
            fonts.remove(fnt)
            fonts=[fnt,*fonts]
        else:
            fonts[0]=fnt
            if gfont:
                fmap[fnt]=__gr.themes.GoogleFont(fnt)
            else:
                fmap[fnt]=fnt
    return [fmap[f] for f in fonts]

def _themeFa(theme_name:str,base_font:str|None=None,font_mono:str|None=None,**kwargs) -> __gr.themes.ThemeClass:
    fmap={
        'Shabnam':'Shabnam',
        'Lateef':__gr.themes.GoogleFont('Lateef'),
        'Vazirmatn':__gr.themes.GoogleFont('Vazirmatn'),
        'Noto Sans Arabic':__gr.themes.GoogleFont('Noto Sans Arabic'),
        'Vazir Code':'Vazir Code',
        'Noto Sans Mono':__gr.themes.GoogleFont('Noto Sans Mono'),
        'Inconsolata':__gr.themes.GoogleFont('Noto Sans Mono'),
        'monospace':'monospace'
    }
    fonts=['Shabnam','Lateef','Vazirmatn','Noto Sans Arabic']
    monofonts=['Vazir Code','Noto Sans Mono','Inconsolata','monospace']
    return _theme(theme_name,
                 font=_set_a_default_font(base_font,fonts,fmap),
                 font_mono=_set_a_default_font(font_mono,monofonts,fmap) ,**kwargs)

def theme(app_schema,**kwargs) -> __gr.themes.ThemeClass:
    return _theme( app_schema.get('THEME'), **kwargs)

def themeFa(app_schema,**kwargs) -> __gr.themes.ThemeClass:
    return _themeFa( app_schema.get('THEME'), app_schema.get('FONT_BASE'), app_schema.get('FONT_MONO'), **kwargs)

def head():
    _font_load_head='''
    <link href="https://cdn.jsdelivr.net/gh/rastikerdar/shabnam-font@v5.0.1/dist/font-face.css" rel="stylesheet" type="text/css" />
    <link href="https://cdn.jsdelivr.net/gh/rastikerdar/vazir-code-font@v1.1.2/dist/font-face.css" rel="stylesheet" type="text/css" />
    '''
    return _font_load_head

def css(agradeintbackground=False,table_safestyle=False):
    _rtl_css='''
    html{direction:rtl !important;}
    body{direction: rtl !important;}
    * { direction: inherit !important; }
    table{direction: rtl !important;}
    '''
    _align_center_css="{text-align: center; display:block;}\n"
    _headings_center_css=_align_center_css.join(['h1 ','h2 ','h3 ',''])
    _footer_css="""
    footer { display: none !important; }
    .footer {
    position: fixed;
    left: 0;
    bottom: 0;
    width: 100%;
    background-color: gray;
    color: black;
    text-align: center;
    direction: ltr;
    }
    """
    _fonts_css='''
    @font-face {
    font-family: Shabnam;
    src: url('Shabnam.eot');
    src: url('Shabnam.eot?#iefix') format('embedded-opentype'),
       url('Shabnam.woff2') format('woff2'),
       url('Shabnam.woff') format('woff'),
       url('Shabnam.ttf') format('truetype');
    font-weight: normal;
    }
    @font-face {
    font-family: Shabnam;
    src: url('Shabnam-Bold.eot');
    src: url('Shabnam-Bold.eot?#iefix') format('embedded-opentype'),
       url('Shabnam-Bold.woff2') format('woff2'),
       url('Shabnam-Bold.woff') format('woff'),
       url('Shabnam-Bold.ttf') format('truetype');
    font-weight: bold;
    }
    @font-face {
    font-family: Shabnam;
    src: url('Shabnam-Thin.eot');
    src: url('Shabnam-Thin.eot?#iefix') format('embedded-opentype'),
       url('Shabnam-Thin.woff2') format('woff2'),
       url('Shabnam-Thin.woff') format('woff'),
       url('Shabnam-Thin.ttf') format('truetype');
    font-weight: 100;
    }
    @font-face {
    font-family: Shabnam;
    src: url('Shabnam-Light.eot');
    src: url('Shabnam-Light.eot?#iefix') format('embedded-opentype'),
       url('Shabnam-Light.woff2') format('woff2'),
       url('Shabnam-Light.woff') format('woff'),
       url('Shabnam-Light.ttf') format('truetype');
    font-weight: 300;
    }
    @font-face {
    font-family: Shabnam;
    src: url('Shabnam-Medium.eot');
    src: url('Shabnam-Medium.eot?#iefix') format('embedded-opentype'),
       url('Shabnam-Medium.woff2') format('woff2'),
       url('Shabnam-Medium.woff') format('woff'),
       url('Shabnam-Medium.ttf') format('truetype');
    font-weight: 500;
    }
    @font-face {
    font-family: Vazir Code;
    src: url('Vazir-Code.eot');
    src: url('Vazir-Code.eot?#iefix') format('embedded-opentype'),
       url('Vazir-Code.woff') format('woff'),
       url('Vazir-Code.ttf') format('truetype');
    font-weight: normal;
    }
    '''
    _code='''
    code {
    font-family: 'Vazir Code', 'Vazir Code Hack', monospaced;
    }
    '''
    _pre='''
    pre {
    font-family: 'Lateef','Vazir Code',Inconsolata,monospace;
    font-size: 16px;
    font-style: italic;
    white-space: pre-line;
    overflow-wrap: normal;
    padding-left:1.5em;
    padding-right:0.5em;
    padding-top:0.5em;
    padding-bottom:0.5em;
    direction: rtl;
    text-align: right;
    }
    blockquote {
    max-width: 90%;
    }
    details > *:not(summary) {
    margin-block-start: 2px !important;
    margin-block-end: 0.7em !important;
    }
    '''
    _ref_section_title='''
    .ref-section-title {
    font-size: 1.1em;
    font-weight: bold;
    text-align: right;
    margin: 0 0;
    width: 100%;
    font-family: inherit;
    line-height: normal;
    padding: 0;
    }
    .hr-ref-section {
    margin-top: 0.7em;
    margin-bottom: 2px;
    margin-left:0;
    width:25%;
    }
    '''
    _select='''
    select {
    direction: rtl !important;
    text-align: left !important;
    }
    '''
    _gradeintbackground='''
    .gradio-container {
    background: rgb(240,240,200);
    background: linear-gradient(0deg, rgba(205,220,230,0.9) 0%,  rgba(208,230,240,1) 6%, rgba(185,205,55,0.7) 10%, rgba(240,235,205,0.65) 25%, rgba(185,205,225,0.55) 100%); 
    }
    '''
    _table_safestyle='''
    table {
    display: block !important;;
    overflow: auto !important;
    }
    '''
    _text_blur='''
    .text-blur1 {
      color: transparent;
      text-shadow: 0 0 1px rgba(255, 255, 255, 0.7); /* X-offset, Y-offset, blur, color */
    }
    .text-blur2 {
      color: transparent;
      text-shadow: 0 0 2px rgba(255, 255, 255, 0.65); /* X-offset, Y-offset, blur, color */
    }
    .text-blur3 {
      color: transparent;
      text-shadow: 0 0 2px rgba(255, 255, 255, 0.55); /* X-offset, Y-offset, blur, color */
    }
    '''
    # _gradeintbackground='''
    # .gradio-container {
    # background: rgb(240,240,200);
    # background: linear-gradient(0deg, rgba(24,35,47,0.9) 0%,  rgba(14,25,47,1) 10%, rgba(165,25,35,0.7) 20%, rgba(11,40,48,0.65) 40%, rgba(34,31,0,0.55) 100%); 
    # }
    # '''
    extra=''
    if agradeintbackground:
        extra+=_gradeintbackground
    if table_safestyle:
        extra+=_table_safestyle
    return "\n".join([
        _rtl_css,
        _headings_center_css,
        _footer_css,
        _fonts_css,
        _code,
        _pre,
        _ref_section_title,
        _select,
        _text_blur,
        extra
    ])
