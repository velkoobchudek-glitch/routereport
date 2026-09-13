# -*- coding: utf-8 -*-
import os
import csv
import sys
import io
import urllib.parse
import unicodedata
from datetime import datetime

import streamlit as st
import pandas as pd

# Globální mobilní nastavení aplikace RouteReport
st.set_page_config(
    page_title="RouteReport",
    page_icon="📱",
    layout="centered",
    initial_sidebar_state="collapsed"
)

EXPORT_FILE = "routereport_zapisy_schuzek.txt"
ULOZENY_ADRESAR_FILE = "cached_customer_db.csv"
HISTORIE_SOUBOR = "crm_historie_schuzek.csv"

# Slovník pro kompletní mezinárodní lokalizaci (Čeština a Angličtina)
LANG = {
    "CS": {
        "title": "📱 RouteReport - Asistent v terénu",
        "cfg_sec": "⚙️ Nastavení databáze zákazníků a e-mailu",
        "cfg_info": "Nahrajte soubor Excel (.xlsx)/CSV a zadejte e-mail šéfa. Aplikace si vše trvale zapamatuje.",
        "upload_lbl": "Vyberte soubor (Excel nebo CSV):",
        "email_boss_lbl": "E-mailová adresa zaměstnavatele / šéfa (pro automatické odesílání):",
        "db_loaded_ok": "✅ Adresář zákazníků i e-mail jsou bezpečně uloženy v mobilu.",
        "db_change_btn": "🔄 Aktualizovat databázi / Změnit e-mail šéfa",
        "sec_1": "1. Datum, čas a trvání schůzky",
        "date_lbl": "Datum:",
        "time_lbl": "Čas návštěvy:",
        "duration_lbl": "Trvání schůzky:",
        "sec_2": "2. Vyhledat a vybrat klienta",
        "search_hint": "Začněte psát jméno klienta nebo město (bez háčků a čárek)...",
        "select_prompt": "-- Klikněte pro výběr klienta --",
        "selected_ok": "🤝 Vybráno pro zápis:",
        "no_client": "❌ Žádný klient neodpovídá zadání.",
        "sec_3": "3. Situace z terénu a slevy",
        "b2b_lbl": "Bude zaslán přístup na B2B",
        "no_interest": "Nemá zájem - bere od jiných",
        "samples_lbl": "Předvedeny vzorky značek:",
        "discount_lbl": "Slíbená sleva na hlavní značku (%):",
        "competitor_lbl": "Hlavní konkurence na prodejně:",
        "potential_lbl": "Potenciál odběru prodejny (%):",
        "sec_4": "4. Průběh jednání a poznámky",
        "note_lbl": "Napište průběh jednání nebo výsledek návštěvy:",
        "remind_check": "Naplánovat termín příštího kontaktu / ozvání",
        "remind_date": "Kdy se ozvat znovu:",
        "btn_save": "💾 ZAPSAT SCHŮZKU DO HISTORIE",
        "save_success": "✅ Schůzka úspěšně uložena a zapsána!",
        "copy_title": "📋 Text ke zkopírování do vašeho systému / e-mailu:",
        "out_date": "📅 DATUM A ČAS",
        "out_dur": "⏱️ TRVÁNÍ",
        "out_client": "🏢 KLIENT",
        "out_sit": "📌 SITUACE",
        "out_disc": "💰 SLEVY ZNAČEK",
        "out_comp": "⚔️ KONKURENCE",
        "out_pot": "📊 POTENCIÁL",
        "out_note": "📝 POZNÁMKA",
        "out_remind": "📞 OZVAT SE"
    },
    "EN": {
        "title": "📱 RouteReport - Field Sales Assistant",
        "cfg_sec": "⚙️ Customer Database & Email Settings",
        "cfg_info": "Upload an Excel (.xlsx)/CSV file and enter your boss's email. The app will remember it permanently.",
        "upload_lbl": "Select database file (Excel or CSV):",
        "email_boss_lbl": "Employer / Boss Email Address (for auto-sending):",
        "db_loaded_ok": "✅ Customer database and email are permanently saved in your mobile.",
        "db_change_btn": "🔄 Update Database / Change Boss Email",
        "sec_1": "1. Date, Time and Duration of the Meeting",
        "date_lbl": "Date:",
        "time_lbl": "Visit Time:",
        "duration_lbl": "Meeting Duration:",
        "sec_2": "2. Search and Select Client",
        "search_hint": "Type client name or city (accents ignored)...",
        "select_prompt": "-- Click to select a client --",
        "selected_ok": "🤝 Selected for report:",
        "no_client": "❌ No client matches your search.",
        "sec_3": "3. Field Situations and Discounts",
        "b2b_lbl": "B2B portal login will be sent",
        "no_interest": "No interest - buys from competitors",
        "samples_lbl": "Samples presented for brands:",
        "discount_lbl": "Promised discount on main brand (%):",
        "competitor_lbl": "Main competitor in store:",
        "potential_lbl": "Store purchase potential (%):",
        "sec_4": "4. Meeting Minutes and Notes",
        "note_lbl": "Write meeting notes or follow-up summary:",
        "remind_check": "Schedule a follow-up date / next contact",
        "remind_date": "When to call again:",
        "btn_save": "💾 SAVE MEETING TO HISTORY",
        "save_success": "✅ Meeting successfully saved to disk!",
        "copy_title": "📋 Text to copy into your email / CRM system:",
        "out_date": "📅 DATE & TIME",
        "out_dur": "⏱️ DURATION",
        "out_client": "🏢 CLIENT",
        "out_sit": "📌 SITUATION",
        "out_disc": "💰 BRAND DISCOUNTS",
        "out_comp": "⚔️ COMPETITOR",
        "out_pot": "📊 POTENTIAL",
        "out_note": "📝 NOTES",
        "out_remind": "📞 FOLLOW UP"
    }
}
def odstran_diakritiku(text):
    if not isinstance(text, str):
        text = str(text)
    return "".join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")

@st.cache_data
def zpracuj_a_ulož_soubor(uploaded_file):
    if uploaded_file is None:
        return None
    try:
        jmeno = uploaded_file.name.lower()
        if jmeno.endswith('.xlsx') or jmeno.endswith('.xls'):
            df = pd.read_excel(uploaded_file, dtype=str, engine='openpyxl')
        else:
            df = pd.read_csv(uploaded_file, sep=None, engine='python', dtype=str)
        
        nove_sloupce = [f"Col_{i}" for i in range(len(df.columns))]
        df.columns = nove_sloupce
        df = df.fillna("")
        
        df.to_csv(ULOZENY_ADRESAR_FILE, index=False, encoding="utf-8")
        return df
    except Exception as e:
        st.error(f"Chyba zpracování Excelu/CSV: {e}")
        return None

def nacti_trvale_ulozeny_adresar():
    if os.path.exists(ULOZENY_ADRESAR_FILE):
        try:
            return pd.read_csv(ULOZENY_ADRESAR_FILE, dtype=str)
        except:
            pass
    return None
def zapis_zaznam_na_disk(klient_radek, datum, cas, trvani, ozvat_se, slevy_data, poznamka, jazyk):
    oddelovac = "=" * 45
    t = LANG[jazyk]
    klient_vystup = " | ".join([str(x) for x in klient_radek[:4] if x])
    
    blok_textu = (
        f"{oddelovac}\n"
        f"{t['out_date']}: {datum.strftime('%d.%m.%Y')} v {cas.strftime('%H:%M')}\n"
        f"{t['out_dur']}:      {trvani} min \n"
        f"{t['out_client']}:      {klient_vystup}\n"
        f"{t['out_sit']}:     {slevy_data['situace']}\n"
        f"{t['out_disc']}:       {slevy_data['sleva']}\n"
        f"{t['out_comp']}:  {slevy_data['konkurence']}\n"
        f"{t['out_pot']}:   {slevy_data['potencial']}\n"
        f"{t['out_note']}:    {poznamka if poznamka else '...'}\n"
        f"{t['out_remind']}:    {ozvat_se.strftime('%d.%m.%Y') if ozvat_se else '---'}\n"
        f"{oddelovac}\n\n"
    )
    
    try:
        with open(EXPORT_FILE, "a", encoding="utf-8") as f:
            f.write(blok_textu)
            
        novy_radek = {
            "Datum": datum.strftime('%d.%m.%Y'),
            "Čas": cas.strftime('%H:%M'),
            "Klient": klient_vystup,
            "Trvání (min)": trvani,
            "Situace": slevy_data['situace'],
            "Slevy Značek": slevy_data['sleva'],
            "Konkurence": slevy_data['konkurence'],
            "Potenciál": slevy_data['potencial'],
            "Poznámka": poznamka if poznamka else ""
        }
        df_novy = pd.DataFrame([novy_radek])
        if os.path.exists(HISTORIE_SOUBOR):
            df_novy.to_csv(HISTORIE_SOUBOR, mode='a', header=False, index=False, encoding="utf-8")
        else:
            df_novy.to_csv(HISTORIE_SOUBOR, mode='w', header=True, index=False, encoding="utf-8")
            
        return blok_textu
    except Exception as e:
        st.error(f"Chyba zápisu souboru: {e}")
        return ""
def vykresli_aplikaci():
    col_lang1, col_lang2 = st.columns(2)
    with col_lang2:
        jazyk = st.selectbox("🌐 Language", ["CS", "EN"], index=0)
        
    t = LANG[jazyk]
    st.title(t["title"])
    
    if "zmena_databaze" not in st.session_state:
        st.session_state["zmena_databaze"] = False

    df_klienti = nacti_trvale_ulozeny_adresar()
    
    email_sefa = st.sidebar.text_input(t["email_boss_lbl"], value=st.session_state.get("boss_email", ""))
    if email_sefa:
        st.session_state["boss_email"] = email_sefa

    if df_klienti is not None and not st.session_state["zmena_databaze"]:
        st.success(t["db_loaded_ok"])
        if st.button(t["db_change_btn"]):
            st.session_state["zmena_databaze"] = True
            st.rerun()
    else:
        with st.expander(t["cfg_sec"], expanded=True):
            st.write(t["cfg_info"])
            email_sefa = st.text_input(t["email_boss_lbl"], value=st.session_state.get("boss_email", ""))
            if email_sefa:
                st.session_state["boss_email"] = email_sefa
                
            nahrany_soubor = st.file_uploader(t["upload_lbl"], type=["csv", "xlsx", "xls", "txt"])
            if nahrany_soubor is not None:
                df_klienti = zpracuj_a_ulož_soubor(nahrany_soubor)
                if df_klienti is not None:
                    st.session_state["zmena_databaze"] = False
                    st.success("👍 Importováno!")
                    st.rerun()

    if df_klienti is None:
        return
    st.subheader(t["sec_1"])
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        datum_sch = st.date_input(t["date_lbl"], datetime.now())
    with col_d2:
        cas_sch = st.time_input(t["time_lbl"], datetime.now())

    st.subheader(t["sec_2"])
    hledat = st.text_input(t["search_hint"], key="crm_hledat_input")
    
    vybrany_klient = None
    klient_cisty_nazev = "Klient"
    
    seznam_moznosti = [t["select_prompt"]]
    vysledky_mapovani = {}
    
    if hledat:
        hledat_ciste = odstran_diakritiku(hledat).lower()
        shoduje_se = df_klienti.apply(
            lambda row: hledat_ciste in odstran_diakritiku(row.astype(str).str.lower().str.cat(sep=' ')), 
            axis=1
        )
        vysledky_hledani = df_klienti[shoduje_se].head(30)
        
        for _, row in vysledky_hledani.iterrows():
            krasny_nazev = " | ".join([str(row.iloc[i]) for i in range(min(len(row), 4)) if row.iloc[i]])
            seznam_moznosti.append(krasny_nazev)
            vysledky_mapovani[krasny_nazev] = row.tolist()
    else:
        for _, row in df_klienti.head(15).iterrows():
            krasny_nazev = " | ".join([str(row.iloc[i]) for i in range(min(len(row), 4)) if row.iloc[i]])
            seznam_moznosti.append(krasny_nazev)
            vysledky_mapovani[krasny_nazev] = row.tolist()

    box_vyber = st.selectbox("🤝 Vyberte klienta:", seznam_moznosti, label_visibility="collapsed")
    
    if box_vyber != t["select_prompt"] and box_vyber in vysledky_mapovani:
        vybrany_klient = vysledky_mapovani[box_vyber]
        klient_cisty_nazev = str(vybrany_klient) if len(vybrany_klient) > 0 else "Klient"
        st.success(f"{t['selected_ok']} {box_vyber}")
    elif hledat and len(seznam_moznosti) == 1:
        st.error(t["no_client"])
    st.subheader(t["sec_3"])
    ch_b2b = st.checkbox(t["b2b_lbl"])
    ch_zajem = st.checkbox(t["no_interest"])
    
    st.caption(t["samples_lbl"])
    c_z1, col_z2, col_z3, col_z4 = st.columns(4)
    with c_z1: m_bbb = st.checkbox("BBB")
    with col_z2: m_cyclon = st.checkbox("CYCLON")
    with col_z3: m_basil = st.checkbox("BASIL")
    with col_z4: m_rozzo = st.checkbox("ROZZO")
    
    zapisane_slevy = {}
    
    if m_bbb:
        zapisane_slevy["BBB"] = st.text_input("Slíbená sleva na BBB (%):", value="", key="sleva_bbb_input")
    if m_cyclon:
        zapisane_slevy["CYCLON"] = st.text_input("Slíbená sleva na CYCLON (%):", value="", key="sleva_cyclon_input")
    if m_basil:
        zapisane_slevy["BASIL"] = st.text_input("Slíbená sleva na BASIL (%):", value="", key="sleva_basil_input")
    if m_rozzo:
        zapisane_slevy["ROZZO"] = st.text_input("Slíbená sleva na ROZZO (%):", value="", key="sleva_rozzo_input")
        
    st.write("") 
    txt_konkurence = st.text_input(t["competitor_lbl"], value="")
    txt_potencial = st.text_input(t["potential_lbl"], value="")

    st.subheader(t["sec_4"])
    obsah_row_frame = st.container()
    col_t1, col_t2 = st.columns(2)
    
    with col_t1:
        skoky_trvani = [str(i) for i in range(5, 125, 5)]
        txt_trvani = st.selectbox(t["duration_lbl"], skoky_trvani, index=5)
        st.write("") 
        ch_ozvat = st.checkbox(t["remind_check"])
        dt_ozvat = st.date_input(t["remind_date"], datetime.now()) if ch_ozvat else None
        
    with col_t2:
        txt_poznamka = st.text_area(t["note_lbl"], height=115)

    st.write("---")
    
    if "posledni_report" not in st.session_state:
        st.session_state["posledni_report"] = ""
    if "posledni_klient" not in st.session_state:
        st.session_state["posledni_klient"] = "Klient"

    if st.button(t["btn_save"], use_container_width=True):
        if not vybrany_klient:
            st.error("❌ Please select a client first / Nejdříve vyberte klienta!")
        else:
            sit_seznam = []
            if ch_b2b: sit_seznam.append("Bude zaslán přístup na B2B")
            if ch_zajem: sit_seznam.append("Nemá zájem - bere od jiných")
            
            zvolene_znacky = [z for z, c in [("BBB", m_bbb), ("CYCLON", m_cyclon), ("BASIL", m_basil), ("ROZZO", m_rozzo)] if c]
            if zvolene_znacky: 
                sit_seznam.insert(0, f"Předvedeny vzorky ({', '.join(zvolene_znacky)})")
            
            slevy_vystup_list = []
            for znacka, hodnota in zapisane_slevy.items():
                if hodnota.strip():
                    slevy_vystup_list.append(f"{znacka}: {hodnota} %")
            sleva_string = ", ".join(slevy_vystup_list) if slevy_vystup_list else "Není"
            
            slevy_objekt = {
                "situace": ", ".join(sit_seznam) if sit_seznam else "Žádná specifická situace",
                "sleva": sleva_string,
                "konkurence": txt_konkurence if txt_konkurence else "Nezadáno",
                "potencial": f"{txt_potencial} %" if txt_potencial else "Nezadáno"
            }
            
            vystupni_blok = zapis_zaznam_na_disk(
                vybrany_klient, datum_sch, cas_sch, txt_trvani, dt_ozvat, slevy_objekt, txt_poznamka, jazyk
            )
            
            if vystupni_blok:
                st.session_state["posledni_report"] = vystupni_blok
                st.session_state["posledni_klient"] = klient_cisty_nazev
                st.success(t["save_success"])
                st.rerun()

    if st.session_state["posledni_report"]:
        st.subheader("✉️ Odeslat hotový report z mobilu:")
        
        text_pro_url = urllib.parse.quote(st.session_state["posledni_report"])
        predmet_pro_url = urllib.parse.quote(f"RouteReport: {st.session_state['posledni_klient']}")
        boss_email_adr = st.session_state.get("boss_email", "")
        
        mail_odkaz = f"mailto:{boss_email_adr}?subject={predmet_pro_url}&body={text_pro_url}"
        st.markdown(f'<a href="{mail_odkaz}" target="_blank" style="text-decoration:none;"><button style="width:100%; height:48px; background-color:#4CAF50; color:white; border:none; border-radius:5px; font-weight:bold; font-size:16px; cursor:pointer;">✉️ ODESLAT REPORT E-MAILEM</button></a>', unsafe_allow_html=True)

        st.subheader(t["copy_title"])
        st.code(st.session_state["posledni_report"])

    st.write("---")
    st.subheader("📋 Přehled zapsaných schůzek")
    
    if os.path.exists(HISTORIE_SOUBOR):
        try:
            df_hist = pd.read_csv(HISTORIE_SOUBOR, dtype=str)
            df_zobrazeni = df_hist.copy()
            df_zobrazeni.index = df_zobrazeni.index + 1
            df_zobrazeni = df_zobrazeni.iloc[::-1]
            st.dataframe(df_zobrazeni, use_container_width=True)
            
            with st.expander("🗑️ Smazat chybný řádek z historie"):
                radek_ke_smaza = st.number_input("Zadejte číslo řádku ke smazání (podle tabulky):", min_value=1, max_value=len(df_hist), step=1)
                if st.button("❌ Definitivně smazat tento řádek", use_container_width=True):
                    df_upraveny = df_hist.drop(df_hist.index[radek_ke_smaza - 1])
                    df_upraveny.to_csv(HISTORIE_SOUBOR, index=False, encoding="utf-8")
                    st.success(f"Řádek {radek_ke_smaza} byl smazán!")
                    st.rerun()
            
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_hist.to_excel(writer, index=False, sheet_name='Schůzky')
            
            st.download_button(
                label="📥 Stáhnout celou historii (Excel)",
                data=buffer.getvalue(),
                file_name=f"crm_report_schuzek_{datetime.now().strftime('%d_%m_%Y')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        except:
            st.caption("Zatím nebyly zapsány žádné schůzky.")
    else:
        st.caption("Zatím nebyly zapsány žádné schůzky.")
if __name__ == "__main__":
    TAJNE_HESLO = "Cestak123"
    
    if "prihlasen" not in st.session_state:
        st.session_state["prihlasen"] = False
        
    if not st.session_state["prihlasen"]:
        st.subheader("🔒 RouteReport - Soukromý přístup")
        vstoupit_heslo = st.text_input("Zadejte přístupové heslo:", type="password")
        
        if st.button("Vstoupit do aplikace", use_container_width=True):
            if vstoupit_heslo == TAJNE_HESLO:
                st.session_state["prihlasen"] = True
                st.rerun()
            else:
                st.error("❌ Nesprávné heslo! Přístup odepřen.")
    else:
        vykresli_aplikaci()
