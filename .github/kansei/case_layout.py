"""Shared presentation of a clinical decision, care choices and related cases.

Only rearranges the editorial context. Readers, media and link destinations
are left intact. The same function is used for the saved pages and generators.
"""
import re

CSS = '/assets/ultrasound-case-guide.20261021.css'


def key_columns(section):
    if 'class="case-context-key-heading"' in section:
        return section
    return re.sub(
        r'(<div class="case-context-key"[^>]*>)(<span class="eyebrow">.*?</h2>)(.*?)(</div>)(?=<div class="case-context-options")',
        lambda m: m[1] + '<header class="case-context-key-heading">' + m[2] + '</header><div class="case-context-key-content">' + m[3] + '</div>' + m[4],
        section, count=1, flags=re.S,
    )


def polish_decision(section):
    if 'class="case-context-options"' in section:
        return key_columns(section)
    start = re.search(r'<h3>Vilket (?:nästa steg|besök) passar ditt besvär\?</h3>', section)
    related = section.index('<h3>Jämför med andra undersökningsfall</h3>')
    assert start and section.endswith('</div></section>')
    clinical, choices, more = section[:start.start()], section[start.end():related], section[related:]

    # Treatment reasoning belongs with the case decision, before care choices.
    note = re.search(r'<div class="hip-case-note"><h3>Var kommer PRP och hyaluron in\?</h3>(.*?)</div>', choices, re.S)
    if note:
        choices = choices[:note.start()] + choices[note.end():]
        disclosure = '<details class="case-context-treatment"><summary>Hur resonerade vi om injektion?</summary>' + note[1] + '</details>'
        assert clinical.endswith('</div>')
        clinical = clinical[:-6] + disclosure + '</div>'

    faq_at = choices.find('<div class="case-context-faq">')
    care, faq = (choices[:faq_at], choices[faq_at:]) if faq_at >= 0 else (choices, '')

    def card(match):
        body = match[1]
        if 'href="/naprapati/"' in body:
            label, title, link = 'Naprapati', 'Behandling och rehabilitering', 'Läs om naprapati och boka'
        elif 'href="/hyaluronsyra/kna/"' in body:
            label, title, link = 'Hyaluronsyra', 'Hyaluron vid knäartros', 'Läs om hyaluron och bokning'
        else:
            label, title, link = 'Ultraljud', 'En riktad undersökning', 'Boka ultraljud'
        body = re.sub(r'<h3>.*?</h3>', '<h3>' + title + '</h3>', body, count=1)
        body = re.sub(r'(<a\b[^>]*>).*?(</a>)', lambda m: m[1] + link + '' + m[2], body, count=1, flags=re.S)
        return '<article><p class="case-context-card-label">' + label + '</p>' + body + '</article>'

    care = re.sub(r'<article>(.*?)</article>', card, care, flags=re.S)
    options = '<div class="case-context-options" aria-labelledby="case-options-title"><header class="case-context-block-heading"><span class="eyebrow">Ditt nästa steg</span><h3 id="case-options-title">Vilken hjälp söker du?</h3></header>' + care + '</div>'

    more = more[:-len('</div></section>')]
    source_at = more.find('<p class="case-context-source">')
    more, source = (more[:source_at], more[source_at:]) if source_at >= 0 else (more, '')
    more = more.replace('<h3>Jämför med andra undersökningsfall</h3>', '<header class="case-context-block-heading"><span class="eyebrow">Fortsätt utforska</span><h3 id="case-related-title">Fler patientfall</h3></header>', 1)
    return key_columns(clinical + options + faq + '<div class="case-context-more" aria-labelledby="case-related-title">' + more + '</div>' + source + '</div></section>')
