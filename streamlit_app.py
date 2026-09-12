# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import os
from datetime import datetime

# Globální mobilní nastavení aplikace RouteReport
st.set_page_config(
    page_title="RouteReport",
    page_icon="📱",
    layout="centered",
    initial_sidebar_state="collapsed"
)

EXPORT_FILE = "routereport_zapisy_schuzek.txt"

# Slovník pro kompletní mezinárodní lokalizaci (Čeština a Angličtina)
LANG = {
    "CS": {
        "title": "📱 RouteReport - Asistent v terénu",
        "cfg_sec": "⚙️ Nastavení databáze zákazníků",
        "cfg_info": "Nahrajte jakýkoliv soubor Excel (.xlsx) nebo CSV se seznamem svých zákazníků z vašeho účetnictví.",
        "upload_lbl": "Vyberte soubor (Excel nebo CSV):",
        "sec_1": "1. Datum, čas a trvání schůzky",
        "date_lbl": "Datum:",
        "time_lbl": "Čas návštěvy:",
        "duration_lbl": "Trvání schůzky:",
        "sec_2": "2. Vyhledat a vybrat klienta",
        "search_hint": "Zadejte jméno klienta nebo město...",
        "select_prompt": "-- Vyberte klienta ze seznamu --",
        "selected_ok": "🤝 Vybráno pro zápis:",
        "no_client": "❌ Žádný klient nenalezen.",
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
        "save_success": "✅ Schůzka úspěšně uložena a zapsána na disk počítače!",
        "copy_title": "📋 Text ke zkopírování do vašeho systému / e-mailu:",
        "out_date": "📅 DATUM A ČAS",
        "out_dur": "⏱️ TRVÁNÍ",
        "out_client": "🏢 KLIENT",
        "out_sit": "📌 SITUACE",
        "out_disc": "💰 SLEVA",
        "out_comp": "⚔️ KONKURENCE",
        "out_pot": "📊 POTENCIÁL",
        "out_note": "📝 POZNÁMKA",
        "out_remind": "📞 OZVAT SE"
    },
    "EN": {
        "title": "📱 RouteReport - Field Sales Assistant",
        "cfg_sec": "⚙️ Customer Database Settings",
        "cfg_info": "Upload any Excel (.xlsx) or CSV file with your customer list exported from your accounting system.",
        "upload_lbl": "Select database file (Excel or CSV):",
        "sec_1": "1. Date, Time and Duration of the Meeting",
        "date_lbl": "Date:",
        "time_lbl": "Visit Time:",
        "duration_lbl": "Meeting Duration:",
        "sec_2": "2. Search and Select Client",
        "search_hint": "Type client name or city...",
        "select_prompt": "-- Select a client from the list --",
        "selected_ok": "🤝 Selected for report:",
        "no_client": "❌ No client found.",
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
        "out_disc": "💰 DISCOUNT",
        "out_comp": "⚔️ COMPETITOR",
        "out_pot": "📊 POTENTIAL",
        "out_note": "📝 NOTES",
        "out_remind": "📞 FOLLOW UP"
    }
}
def nacti_univerzalni_databazi(uploaded_file):
    if uploaded_file is None:
        return None
    try:
        jmeno = uploaded_file.name.lower()
        if jmeno.endswith('.xlsx') or jmeno.endswith('.xls'):
            df = pd.read_excel(uploaded_file, dtype=str)
        else:
            df = pd.read_csv(uploaded_file, sep=None, engine='python', dtype=str)
        
        nove_sloupce = [f"Col_{i}" for i in range(len(df.columns))]
        df.columns = nove_sloupce
        return df.fillna("")
    except Exception as e:
        st.error(f"Error loading file / Chyba načítání souboru: {e}")
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
        return blok_textu
    except Exception as e:
        st.error(f"Chyba zápisu souboru / File write error: {e}")
        return ""
def vykresli_aplikaci():
    col_lang1, col_lang2 = st.columns(2)
    with col_lang2:
        jazyk = st.selectbox("🌐 Language", ["CS", "EN"], index=0)
        
    t = LANG[jazyk]
    st.title(t["title"])
    
    with st.expander(t["cfg_sec"], expanded=True):
        st.write(t["cfg_info"])
        nahrany_soubor = st.file_uploader(t["upload_lbl"], type=["csv", "xlsx", "xls", "txt"])
        
    df_klienti = nacti_univerzalni_databazi(nahrany_soubor)
    if df_klienti is None:
        st.info("💡 [CS] Pro spuštění nahrajte Excel se zákazníky.\n\n💡 [EN] Please upload an Excel file with customers to start.")
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
    if hledat:
        shoda = df_klienti.apply(lambda row: hledat.lower() in row.astype(str).str.lower().str.cat(sep=' '), axis=1)
        vysledky_hledani = df_klienti[shoda]
        
        if not vysledky_hledani.empty:
            seznam_moznosti = [t["select_prompt"]] + [
                " | ".join([str(row.iloc[i]) for i in range(min(len(row), 4)) if row.iloc[i]])
                for _, row in vysledky_hledani.head(15).iterrows()
            ]
            box_vyber = st.selectbox("🔍 Results / Výsledky:", seznam_moznosti)
            
            if box_vyber != t["select_prompt"]:
                idx = seznam_moznosti.index(box_vyber) - 1
                vybrany_klient = vysledky_hledani.iloc[idx].tolist()
                st.success(f"{t['selected_ok']} {vybrany_klient}")
        else:
            st.error(t["no_client"])
    st.subheader(t["sec_3"])
    ch_b2b = st.checkbox(t["b2b_lbl"])
    ch_zajem = st.checkbox(t["no_interest"])
    
    st.caption(t["samples_lbl"])
    c_z1, col_z2, col_z3, col_z4 = st.columns(4)
    with c_z1: m_bbb = st.checkbox("BBB")
    with col_z2: m_cyclon = st.checkbox("CYCLON")
    with col_z3: m_basil = st.checkbox("BASIL")
    with col_z4: m_rozzo = m_rozzo = st.checkbox("ROZZO")
    
    txt_sleva = st.text_input(t["discount_lbl"], value="")
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
            
            slevy_objekt = {
                "situace": ", ".join(sit_seznam) if sit_seznam else "Žádná specifická situace",
                "sleva": f"{txt_sleva} %" if txt_sleva else "Není",
                "konkurence": txt_konkurence if txt_konkurence else "Nezadáno",
                "potencial": f"{txt_potencial} %" if txt_potencial else "Nezadáno"
            }
            
            vystupni_blok = zapis_zaznam_na_disk(
                vybrany_klient, datum_sch, cas_sch, txt_trvani, dt_ozvat, slevy_objekt, txt_poznamka, jazyk
            )
            
            if vystupni_blok:
                st.success(t["save_success"])
                st.subheader(t["copy_title"])
                st.code(vystupni_blok)
# 🔒 Zabezpečení aplikace přístupovým heslem pro vaše soukromé účely
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
