from playwright.sync_api import sync_playwright
import os, re
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

URL = "https://nea.wrt.stellantis.com/parking/#/"

PARKING_OPTION = os.environ["PARKING_OPTION_LABEL"]   # es: "Parcheggio B8-C8 - slot 09:00 - 12:00"
COLONNINA = os.environ["COLONNINA_NAME"]
TARGA = os.environ["LICENSE_PLATE"]

TZ = ZoneInfo("Europe/Rome")

def target_date_plus6():
    # martedì 00:00 (Italia) -> +6 = lunedì successivo
    return (datetime.now(TZ).date() + timedelta(days=6))

def pick_from_dropdown(page, option_text: str):
    """
    Dropdown a tendina: click sul combobox -> click sull'opzione per testo.
    Funziona anche con dropdown custom che espongono role=option.
    """
    # 1) Provo a cliccare il primo combobox visibile (se ne hai più di uno, puoi affinare)
    combo = page.get_by_role("combobox").first
    combo.click()

    # 2) Seleziono l'opzione per nome (testo visibile)
    page.get_by_role("option", name=re.compile(re.escape(option_text), re.I)).click()

def pick_date_from_calendar(page, d):
    """
    Seleziona una data dal calendario.
    Strategia generica:
      - click sul campo data (textbox / input)
      - naviga mesi fino a target (legge header mese/anno)
      - click sul giorno come gridcell
    """
    # 1) Apri il date picker cliccando sul campo data.
    # Qui uso un match ampio: se sai label/placeholder preciso, è meglio.
    date_field = page.get_by_role("textbox").filter(has_text=re.compile("", re.I)).first
    date_field.click()

    # 2) Individuo header mese/anno (molti datepicker hanno un testo tipo "Marzo 2026")
    # Se non esiste, il fallback è cliccare "next month" per un numero di volte.
    target_year = d.year
    target_month = d.month
    target_day = d.day

    # mapping mese ITA per matching quando l'header è in italiano
    mesi_it = ["gennaio","febbraio","marzo","aprile","maggio","giugno","luglio","agosto","settembre","ottobre","novembre","dicembre"]
    target_month_name = mesi_it[target_month-1]

    # Provo a leggere un header “mese anno” e navigare finché non combacia.
    # NOTA: i selettori dell’header e dei bottoni prev/next cambiano a seconda del widget:
    # questi sono pattern comuni, spesso funzionano; altrimenti vanno adattati con codegen.
    header = page.locator("[role='heading'], .calendar-header, .mat-calendar-period-button").first
    next_btn = page.get_by_role("button", name=re.compile("next|successivo|>", re.I)).first

    for _ in range(18):  # massimo 18 mesi per sicurezza
        try:
            text = (header.text_content() or "").strip().lower()
        except Exception:
            text = ""

        # se l'header contiene mese e anno target, seleziono il giorno
        if str(target_year) in text and target_month_name in text:
            break

        # altrimenti vado avanti di un mese
        next_btn.click()

    # 3) Clic sul giorno.
    # Molti datepicker espongono i giorni come role=gridcell o button con il numero.
    # Provo gridcell, poi fallback su testo.
    try:
        page.get_by_role("gridcell", name=str(target_day)).click()
    except Exception:
        page.get_by_text(re.compile(rf"^{target_day}$")).click()

def main():
    d = target_date_plus6()
    print("Now (Rome):", datetime.now(TZ).isoformat())
    print("Target date:", d.isoformat())

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(URL, wait_until="domcontentloaded")

        # 1) dropdown: seleziona B8-C8... (menu a tendina)
        pick_from_dropdown(page, PARKING_OPTION)

        # 2) calendario: seleziona la data +6
        pick_date_from_calendar(page, d)

        # 3) Cerca (prima dei risultati)
        page.get_by_role("button", name=re.compile("^Cerca$", re.I)).click()
        page.wait_for_load_state("networkidle")

        # 4) Solo ora: selezione colonnina e prenota (la tua logica)
        page.get_by_text(COLONNINA).wait_for(timeout=15000)
        page.get_by_text(COLONNINA).scroll_into_view_if_needed()

        page.locator(
            f"xpath=//*[contains(., '{COLONNINA}')]//button[contains(., 'Prenota')]"
        ).click()

        page.locator("input[type='checkbox'], input[type='radio']").first.check()
        page.get_by_role("button", name="NEXT").click()

        page.locator("input, textarea").first.fill(TARGA)
        page.get_by_role("button", name="Salva").click()

        browser.close()

if __name__ == "__main__":
    main()
