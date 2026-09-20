# -*- coding: utf-8 -*-
import os
import csv
import sys
import io
import urllib.parse
import unicodedata
from datetime import datetime, timedelta
import streamlit as st
import pandas as pd
st.set_page_config(
    page_title="RouteReport",
    page_icon="📱",
    layout="centered",
    initial_sidebar_state="collapsed"
)
EXPORT_FILE = "routereport_zapisy_schuzek.txt"
ULOZENY_ADRESAR_FILE = "cached_customer_db.csv"
HISTORIE_SOUBOR = "crm_historie_schuzek.csv"
UKOLY_SOUBOR = "crm_ukoly_kalendar.csv"
LANG = {
    "CS": {
        "title": "📱 RouteReport - Poznámky z terénu",
        "cfg_sec": "⚙️ Nastavení databáze",
        "cfg_info": "Nahrajte soubor CSV se zákazníky a zadejte e-mail šéfa.",
        "upload_lbl": "Vyberte soubor (pouze CSV):",
        "email_boss_lbl": "E-mailová adresa manažera / šéfa:",
        "db_loaded_ok": "✅ Adresář zákazníků i e-mail jsou bezpečně uloženy.",
        "db_change_btn": "🔄 Aktualizovat databázi / Změnit e-mail šéfa",
        "sec_1": "1. Datum, čas a trvání návštěvy",
        "date_lbl": "Datum:",
        "time_lbl": "Čas návštěvy (Hodina / Minuta):",
        "duration_lbl": "Trvání návštěvy:",
        "sec_2": "2. Vyhledat a vybrat klienta",
        "search_hint": "Ťukněte a začněte psát jméno nebo město...",
        "select_prompt": "-- Začněte psát jméno nebo město klienta --",
        "selected_ok": "🤝 Vybráno pro uložení:",
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
        "remind_check": "🔔 Naplánovat termín příštího kontaktu (Vnitřní připomínka)",
        "remind_date": "Kdy se ozvat znovu:",
        "btn_save": "💾 ULOŽIT INFO O NÁVŠTĚVĚ",
        "save_success": "✅ Info o návštěvě úspěšně uloženo!",
        "copy_title": "📋 Text ke zkopírování:",
        "out_date": "📅 DATUM A ČAS",
        "out_dur": "⏱️ TRVÁNÍ",
        "out_client": "🏢 KLIENT",
        "out_sit": "📌 SITUACE",
        "out_disc": "💰 SLEVY ZNAČEK",
        "out_comp": "⚔️ KONKURENCE",
        "out_pot": "📊 POTENCIÁL",
        "out_note": "📝 POZNÁMKA",
        "out_remind": "📞 OZVAT SE"
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
        bytes_data = uploaded_file.read()
        try:
            text_data = bytes_data.decode("utf-8")
            df = pd.read_csv(io.StringIO(text_data), sep=None, engine='python', dtype=str)
        except UnicodeDecodeError:
            text_data = bytes_data.decode("cp1250", errors="replace")
            df = pd.read_csv(io.StringIO(text_data), sep=None, engine='python', dtype=str)
        nove_sloupce = [f"Col_{i}" for i in range(len(df.columns))]
        df.columns = nove_sloupce
        df = df.fillna("")
        df.to_csv(ULOZENY_ADRESAR_FILE, index=False, encoding="utf-8")
        return df
    except Exception as e:
        st.error(f"Chyba: {e}")
        return None

def nacti_trvale_ulozeny_adresar():
    if os.path.exists(ULOZENY_ADRESAR_FILE):
        try: return pd.read_csv(ULOZENY_ADRESAR_FILE, dtype=str)
        except: pass
    return None
def zapis_zaznam_na_disk(klient_radek, datum, cas_text, trvani, ozvat_se, slevy_data, poznamka, jazyk):
    oddelovac = "=" * 45
    t = LANG[jazyk]
    klient_vystup = " | ".join([str(x) for x in klient_radek[:6] if x])
    ciste_jmeno = str(klient_radek).strip() if len(klient_radek) > 0 else "Klient"
    
    cisty_tel = ""
    cisty_mail = ""
    for policko in [str(x).strip() for x in klient_radek]:
        if "@" in policko: cisty_mail = policko
        elif policko.isdigit() and len(policko) >= 9: cisty_tel = policko
        elif ("+" in policko) and len(policko) >= 10: cisty_tel = policko
            
    blok_textu = (
        f"{oddelovac}\n"
        f"{t['out_date']}: {datum.strftime('%d.%m.%Y')} v {cas_text}\n"
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
        with open(EXPORT_FILE, "a", encoding="utf-8") as f: f.write(blok_textu)
        novy_radek = {
            "Datum": datum.strftime('%d.%m.%Y'), "Čas": cas_text, "Klient": klient_vystup, "Trvání (min)": trvani,
            "Situace": slevy_data['situace'], "Slevy Značek": slevy_data['sleva'], "Konkurence": slevy_data['konkurence'],
            "Potenciál": slevy_data['potencial'], "Poznámka": poznamka if poznamka else "", "RawText_Zaloha": blok_textu
        }
        df_novy = pd.DataFrame([novy_radek])
        if os.path.exists(HISTORIE_SOUBOR): df_novy.to_csv(HISTORIE_SOUBOR, mode='a', header=False, index=False, encoding="utf-8")
        else: df_novy.to_csv(HISTORIE_SOUBOR, mode='w', header=True, index=False, encoding="utf-8")
        if ozvat_se:
            novy_ukol = {"Termín": ozvat_se.strftime('%d.%m.%Y'), "Klient": ciste_jmeno, "Telefon": cisty_tel, "Email": cisty_mail, "Důvod (Kvůli čemu)": f"Slevy: {slevy_data['sleva']}. {poznamka}"}
            df_ukol = pd.DataFrame([novy_ukol])
            if os.path.exists(UKOLY_SOUBOR): df_ukol.to_csv(UKOLY_SOUBOR, mode='a', header=False, index=False, encoding="utf-8")
            else: df_ukol.to_csv(UKOLY_SOUBOR, mode='w', header=True, index=False, encoding="utf-8")
        return blok_textu
    except: return ""
def vykresli_aplikaci():
    jazyk = "CS"
    t = LANG[jazyk]
    
    if os.path.exists(UKOLY_SOUBOR):
        try:
            df_kontrol_u = pd.read_csv(UKOLY_SOUBOR, dtype=str)
            if not df_kontrol_u.empty:
                dnes_str = datetime.utcnow().strftime('%d.%m.%Y')
                shody_dnes = df_kontrol_u[df_kontrol_u["Termín"] == dnes_str]
                if len(shody_dnes) > 0 and "popup_odkliknuto" not in st.session_state:
                    @st.dialog("🔔 DNEŠNÍ URGENTNÍ ÚKOLY")
                    def ranni_popup_okno():
                        st.error(f"⚠️ Dnes máte naplánované {len(shody_dnes)} úkoly:")
                        for _, r_u in shody_dnes.iterrows():
                            st.markdown(f"🏢 **Klient:** {r_u['Klient']}\n📝 **Úkol:** {r_u['Důvod (Kvůli čemu)']}")
                        if st.button("Rozumím 👍", use_container_width=True):
                            st.session_state["popup_odkliknuto"] = True
                            st.rerun()
                    ranni_popup_okno()
        except: pass

    if "zmena_databaze" not in st.session_state: st.session_state["zmena_databaze"] = False
    df_klienti = nacti_trvale_ulozeny_adresar()
    email_sefa = st.sidebar.text_input(t["email_boss_lbl"], value=st.session_state.get("boss_email", ""))
    if email_sefa: st.session_state["boss_email"] = email_sefa

    if df_klienti is not None and not st.session_state["zmena_databaze"]:
        st.success(t["db_loaded_ok"])
        if st.button(t["db_change_btn"]):
            st.session_state["zmena_databaze"] = True
            st.rerun()
    else:
        with st.expander(t["cfg_sec"], expanded=True):
            email_sefa = st.text_input(t["email_boss_lbl"], value=st.session_state.get("boss_email", ""))
            if email_sefa: st.session_state["boss_email"] = email_sefa
            nahrany_soubor = st.file_uploader(t["upload_lbl"], type=["csv", "txt"])
            if nahrany_soubor is not None:
                df_klienti = zpracuj_a_ulož_soubor(nahrany_soubor)
                if df_klienti is not None:
                    st.session_state["zmena_databaze"] = False
                    st.rerun()
    if df_klienti is None: return
    st.subheader(t["sec_1"])
    col_d1, col_t_h, col_t_m = st.columns(3)
    
    # Čistý výpočet času posunutého o 10 minut dopředu bez chybových knihoven
    cas_ted_plus_10 = datetime.utcnow() + timedelta(hours=2) + timedelta(minutes=10)
    akt_h = cas_ted_plus_10.hour
    akt_m = cas_ted_plus_10.minute
    
    # Matematické zaokrouhlení minut dolů na nejbližší pětku, aby to sedělo do seznamu
    zaok_m = int(5 * (akt_m // 5))
    if zaok_m >= 60: zaok_m = 55

    with col_d1: datum_sch = st.date_input(t["date_lbl"], cas_ted_plus_10.date())
    with col_t_h:
        hodiny_list = [f"{i:02d}" for i in range(24)]
        zvolena_hodina = st.selectbox("Hodina:", hodiny_list, index=akt_h)
    with col_t_m:
        minuty_list = [f"{i:02d}" for i in range(0, 60, 5)]
        zvolen_minuta = st.selectbox("Minuta:", minuty_list, index=minuty_list.index(f"{zaok_m:02d}"))
    cas_vystup_text = f"{zvolena_hodina}:{zvolen_minuta}"

    st.subheader(t["sec_2"])
    seznam_zakazniku, mapovani_zaznamu = [], {}
    for _, row in df_klienti.iterrows():
        krasny_text = " | ".join([str(row.iloc[i]) for i in range(min(len(row), 6)) if row.iloc[i]])
        seznam_zakazniku.append(krasny_text)
        mapovani_zaznamu[krasny_text] = row.tolist()

    vybrany_box_text = st.selectbox(t["search_hint"], options=seznam_zakazniku, index=None, placeholder=t["select_prompt"])
    vybrany_klient = None
    if vybrany_box_text and vybrany_box_text in mapovani_zaznamu:
        vybrany_klient = mapovani_zaznamu[vybrany_box_text]
        st.success(f"{t['selected_ok']} {vybrany_box_text}")
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
    if m_bbb: zapisane_slevy["BBB"] = st.text_input("Sleva BBB (%):", value="", key="sl_bbb")
    if m_cyclon: zapisane_slevy["CYCLON"] = st.text_input("Sleva CYCLON (%):", value="", key="sl_cyc")
    if m_basil: zapisane_slevy["BASIL"] = st.text_input("Sleva BASIL (%):", value="", key="sl_bas")
    if m_rozzo: zapisane_slevy["ROZZO"] = st.text_input("Sleva ROZZO (%):", value="", key="sl_roz")
        
    txt_konkurence = st.text_input(t["competitor_lbl"], value="")
    txt_potencial = st.text_input(t["potential_lbl"], value="")
    st.subheader(t["sec_4"])
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        txt_trvani = st.selectbox(t["duration_lbl"], [str(i) for i in range(5, 125, 5)], index=5)
        ch_ozvat = st.checkbox(t["remind_check"])
        dt_ozvat = st.date_input(t["remind_date"], (datetime.utcnow() + timedelta(hours=2)).date()) if ch_ozvat else None
    with col_t2: txt_poznamka = st.text_area(t["note_lbl"], height=115)
    st.write("---")
    if st.button(t["btn_save"], use_container_width=True):
        if not vybrany_klient: st.error("❌ Vyberte klienta!")
        else:
            sit_seznam = []
            if ch_b2b: sit_seznam.append("Bude zaslán přístup na B2B")
            if ch_zajem: sit_seznam.append("Nemá zájem - bere od jiných")
            zvolene_znacky = [z for z, c in [("BBB", m_bbb), ("CYCLON", m_cyclon), ("BASIL", m_basil), ("ROZZO", m_rozzo)] if c]
            if zvolene_znacky: sit_seznam.insert(0, f"Předvedeny vzorky ({', '.join(zvolene_znacky)})")
            slevy_vystup_list = [f"{znacka}: {hodnota} %" for znacka, hodnota in zapisane_slevy.items() if hodnota.strip()]
            slevy_objekt = {
                "situace": ", ".join(sit_seznam) if sit_seznam else "Žádná specifická situace",
                "sleva": ", ".join(slevy_vystup_list) if slevy_vystup_list else "Není",
                "konkurence": txt_konkurence if txt_konkurence else "Nezadáno", "potencial": f"{txt_potencial} %" if txt_potencial else "Nezadáno"
            }
            if zapis_zaznam_na_disk(vybrany_klient, datum_sch, cas_vystup_text, txt_trvani, dt_ozvat, slevy_objekt, txt_poznamka, jazyk):
                st.success(t["save_success"])
                st.rerun()

    st.write("---")
    st.subheader("📋 Deník mých návštěv")
    if os.path.exists(HISTORIE_SOUBOR):
        try:
            df_hist = pd.read_csv(HISTORIE_SOUBOR, dtype=str)
            df_zobrazeni = df_hist.copy()
            if "RawText_Zaloha" in df_zobrazeni.columns: df_zobrazeni = df_zobrazeni.drop(columns=["RawText_Zaloha"])
            st.dataframe(df_zobrazeni.iloc[::-1], use_container_width=True)
            kompletni_text_mailu = "\n".join(df_hist["RawText_Zaloha"].tolist()) if "RawText_Zaloha" in df_hist.columns else ""
            mail_odkaz = f"mailto:{st.session_state.get('boss_email', '')}?subject={urllib.parse.quote('RouteReport')}&body={urllib.parse.quote(kompletni_text_mailu)}"
            st.markdown(f'<a href="{mail_odkaz}" target="_blank"><button style="width:100%; height:52px; background-color:#1E88E5; color:white; border:none; border-radius:5px; font-weight:bold;">✉️ ODESLAT MANAŽEROVI</button></a>', unsafe_allow_html=True)
        except: pass
    st.write("---")
    st.subheader("📅 Moje vnitřní připomínky a úkoly")
    if os.path.exists(UKOLY_SOUBOR):
        try:
            df_ukoly = pd.read_csv(UKOLY_SOUBOR, dtype=str)
            if not df_ukoly.empty:
                dnes_dt = (datetime.utcnow() + timedelta(hours=2)).date()
                for idx, row_u in df_ukoly.iterrows():
                    try:
                        t_date = datetime.strptime(row_u["Termín"], "%d.%m.%Y").date()
                        status_badge = "🔴 HOŘÍ!" if (t_date - dnes_dt).days < 0 else "🟢 V plánu"
                    except: status_badge = "🟢 V plánu"
                    with st.container(border=True):
                        st.markdown(f"**{status_badge}** | 📅 {row_u['Termín']} | 🏢 {row_u['Klient']}\n\n📝 Důvod: {row_u['Důvod (Kvůli čemu)']}")
                        col_c1, col_c2 = st.columns(2)
                        tel_val = str(row_u['Telefon']).strip() if 'Telefon' in row_u and pd.notna(row_u['Telefon']) else ""
                        mail_val = str(row_u['Email']).strip() if 'Email' in row_u and pd.notna(row_u['Email']) else ""
                        with col_c1:
                            if tel_val and tel_val != "nan" and tel_val != "": st.markdown(f'<a href="tel:{tel_val}"><button style="width:100%; height:36px; background-color:#2E7D32; color:white; border:none; border-radius:5px; font-weight:bold; font-size:11px;">📞 VOLAT: {tel_val}</button></a>', unsafe_allow_html=True)
                        with col_c2:
                            if mail_val and mail_val != "nan" and mail_val != "": st.markdown(f'<a href="mailto:{mail_val}"><button style="width:100%; height:36px; background-color:#1565C0; color:white; border:none; border-radius:5px; font-weight:bold; font-size:11px;">✉️ E-MAIL</button></a>', unsafe_allow_html=True)
                        if st.button("✅ Vyřízeno", key=f"del_{idx}", use_container_width=True):
                            df_ukoly.drop(df_ukoly.index[idx]).to_csv(UKOLY_SOUBOR, index=False, encoding="utf-8")
                            st.rerun()
            else: st.caption("Žádné připomínky.")
        except: st.caption("Žádné připomínky.")
    else: st.caption("Žádné připomínky.")

    st.write("---")
    with st.expander("🗑️ Čistění deníku"):
        if st.button("🚨 VYČISTIT ÚPLNĚ VŠE", use_container_width=True):
            for f in [HISTORIE_SOUBOR, EXPORT_FILE, UKOLY_SOUBOR]:
                if os.path.exists(f): os.remove(f)
            st.rerun()
    if os.path.exists(HISTORIE_SOUBOR):
        st.download_button(label="📥 Stáhnout zálohu (.csv)", data=pd.read_csv(HISTORIE_SOUBOR).to_csv(index=False, encoding="utf-8"), file_name="routereport.csv", mime="text/csv", use_container_width=True)
if __name__ == "__main__":
    TAJNE_HESLO = "Cestak123"
    if "prihlasen_trvale" not in st.session_state: st.session_state["prihlasen_trvale"] = False
    if not st.session_state["prihlasen_trvale"]:
        st.subheader("🔒 RouteReport - Private Access")
        vstoupit_heslo = st.text_input("Heslo:", type="password")
        if st.button("Vstoupit", use_container_width=True):
            if vstoupit_heslo == TAJNE_HESLO:
                st.session_state["prihlasen_trvale"] = True
                st.rerun()
            else: st.error("❌ Špatné heslo!")
    else: vykresli_aplikaci()
