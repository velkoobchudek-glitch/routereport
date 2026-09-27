# -*- coding: utf-8 -*-
import os
import csv
import sys
import io
import urllib.parse
import unicodedata
import time
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
UZIVATEL_SOUBOR = "crm_profil_uzivatele.csv"
LANG = {
    "CS": {
        "title": "📱 RouteReport - Poznámky z terénu",
        "cfg_sec": "⚙️ Globální nastavení systému a profilu",
        "cfg_info": "Zadejte konfiguraci značek, e-mail manažera, jméno reportéra a nahrajte adresář.",
        "upload_lbl": "KROK 3: Vyberte soubor s klienty z Pohody (CSV):",
        "email_boss_lbl": "E-mailová adresa manažera / šéfa:",
        "db_loaded_ok": "✅ Systém je plně nakonfigurován a připraven k práci.",
        "db_change_btn": "⚙️ OTEVŘÍT GLOBÁLNÍ NASTAVENÍ SYSTÉMU (ZNAČKY / PROFIL / ADRESY)",
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
def nacti_profil_uzivatele():
    if os.path.exists(UZIVATEL_SOUBOR):
        try:
            df = pd.read_csv(UZIVATEL_SOUBOR, dtype=str)
            if not df.empty:
                return {"jmeno": str(df.iloc[0]["jmeno"]), "telefon": str(df.iloc[0]["telefon"])}
        except: pass
    return {"jmeno": "Jakub Holan", "telefon": "608470900"}

def uloz_profil_uzivatele(jmeno, telephone):
    try:
        df = pd.DataFrame([{"jmeno": jmeno, "telefon": telephone}])
        df.to_csv(UZIVATEL_SOUBOR, index=False, encoding="utf-8")
    except: pass
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
        st.error(f"Chyba zpracování: {e}")
        return None

def nacti_trvale_ulozeny_adresar():
    if os.path.exists(ULOZENY_ADRESAR_FILE):
        try: return pd.read_csv(ULOZENY_ADRESAR_FILE, dtype=str)
        except: pass
    return None
def zapis_zaznam_na_disk(klient_vystup, datum, cas_text, trvani, ozvat_se, slevy_data, poznamka, jazyk, surovy_radek_klienta=None):
    oddelovac = "=" * 45
    t = LANG[jazyk]
    ciste_jmeno = str(klient_vystup).replace(" | ", " ").strip()
    prof = nacti_profil_uzivatele()
    
    cisty_tel, cisty_mail = "", ""
    if surovy_radek_klienta is not None:
        for bunka in [str(x).strip() for x in surovy_radek_klienta]:
            if "@" in bunka: cisty_mail = bunka
            elif bunka.startswith("http") or bunka.startswith("www."): pass
            else:
                c_tel = bunka.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
                if c_tel.replace("+", "").isdigit() and len(c_tel.replace("+", "")) >= 9: cisty_tel = c_tel

    termin_kontakt = ozvat_se.strftime('%d.%m.%Y') if ozvat_se else '---'

    blok_textu = (
        f"{oddelovac}\n"
        f"👤 OBCHODNÍK:  {prof.get('jmeno', 'Jakub Holan')} ({prof.get('telefon', '608470900')})\n"
        f"{t['out_date']}: {datum.strftime('%d.%m.%Y')} v {cas_text}\n"
        f"{t['out_dur']}:      {trvani} min \n"
        f"{t['out_client']}:      {klient_vystup}\n"
        f"{t['out_sit']}:     {slevy_data['situace']}\n"
        f"{t['out_disc']}:       {slevy_data['sleva']}\n"
        f"{t['out_comp']}:  {slevy_data['konkurence']}\n"
        f"{t['out_pot']}:   {slevy_data['potencial']}\n"
        f"{t['out_note']}:    {poznamka if poznamka else '...'}\n"
        f"{t['out_remind']}:    {termin_kontakt}\n"
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
            unikatni_id_ukolu = f"ID_{int(time.time() * 1000)}"
            novy_ukol = {
                "TaskID": unikatni_id_ukolu, "Termín": ozvat_se.strftime('%d.%m.%Y'), "Klient": ciste_jmeno[:120], 
                "Telefon": cisty_tel if cisty_tel else "Nezadáno", "Email": cisty_mail if cisty_mail else "Nezadáno", 
                "Důvod (Kvůli čemu)": f"Slevy: {slevy_data['sleva']}. {poznamka}"
            }
            df_ukol = pd.DataFrame([novy_ukol])
            if os.path.exists(UKOLY_SOUBOR): df_ukol.to_csv(UKOLY_SOUBOR, mode='a', header=False, index=False, encoding="utf-8")
            else: df_ukol.to_csv(UKOLY_SOUBOR, mode='w', header=True, index=False, encoding="utf-8")
        return blok_textu
    except: return ""

def obnov_data_ze_zalohy_backend(soubor_objekt):
    try:
        bytes_z = soubor_objekt.read()
        text_z = bytes_z.decode("utf-8", errors="ignore")
        if "===UKOLY_SEPARATOR===" in text_z:
            casti_textu = text_z.split("===UKOLY_SEPARATOR===\n")
            text_historie = casti_textu[0]
            text_ukoly = casti_textu[1] if len(casti_textu) > 1 else ""
            
            lines_h = [l for l in text_historie.splitlines() if l.strip() and "#ERROR!" not in l]
            if lines_h:
                df_imp_h = pd.read_csv(io.StringIO("\n".join(lines_h)), dtype=str)
                df_imp_h = df_imp_h[df_imp_h['Datum'].str.contains(r'\d', na=False, regex=True)]
                df_imp_h.to_csv(HISTORIE_SOUBOR, index=False, encoding="utf-8")
            
            if text_ukoly.strip():
                lines_u = [l for l in text_ukoly.splitlines() if l.strip() and "#ERROR!" not in l]
                if lines_u:
                    df_imp_u = pd.read_csv(io.StringIO("\n".join(lines_u)), dtype=str)
                    df_imp_u = df_imp_u[df_imp_u['Termín'].str.contains(r'\d', na=False, regex=True)]
                    df_imp_u.to_csv(UKOLY_SOUBOR, index=False, encoding="utf-8")
            elif os.path.exists(UKOLY_SOUBOR): os.remove(UKOLY_SOUBOR)
        else:
            lines_fallback = [l for l in text_z.splitlines() if l.strip() and "#ERROR!" not in l]
            df_import_starší = pd.read_csv(io.StringIO("\n".join(lines_fallback)), dtype=str)
            df_import_starší = df_import_starší[df_import_starší['Datum'].str.contains(r'\d', na=False, regex=True)]
            df_import_starší.to_csv(HISTORIE_SOUBOR, index=False, encoding="utf-8")
        return True
    except: return False
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
    prof = nacti_profil_uzivatele()
    
    email_sefa = st.sidebar.text_input(t["email_boss_lbl"], value=st.session_state.get("boss_email", "manager@firma.cz"))
    if email_sefa: st.session_state["boss_email"] = email_sefa

    if "brand_name_1" not in st.session_state: st.session_state["brand_name_1"] = "BBB"
    if "brand_name_2" not in st.session_state: st.session_state["brand_name_2"] = "BASIL"
    if "brand_name_3" not in st.session_state: st.session_state["brand_name_3"] = "ROZZO"
    if "brand_name_4" not in st.session_state: st.session_state["brand_name_4"] = ""

    if df_klienti is not None and not st.session_state["zmena_databaze"]:
        st.success(t["db_loaded_ok"])
        if st.button(t["db_change_btn"], use_container_width=True):
            st.session_state["zmena_databaze"] = True
            st.rerun()
    else:
        with st.expander(t["cfg_sec"], expanded=True):
            st.markdown("### 👤 1. Profil obchodního zástupce (Skryté nastavení)")
            col_p1, col_p2 = st.columns(2)
            with col_p1: u_jmeno = st.text_input("Moje Jméno a Příjmení:", value=prof.get("jmeno", "Jakub Holan"))
            with col_p2: u_tel = st.text_input("Můj Firemní Telefon:", value=prof.get("telefon", "608470900"))
            if u_jmeno != prof.get("jmeno") or u_tel != prof.get("telefon"):
                uloz_profil_uzivatele(u_jmeno.strip(), u_tel.strip())

            st.markdown("### ⚙️ 2. Pojmenování produktových řad / značek")
            st.caption("💡 Nechte políčko prázdné, pokud značku nechcete v aplikaci vůbec ukazovat.")
            col_b1, col_b2 = st.columns(2)
            with col_b1:
                b1 = st.text_input("Název Značky 1:", value=st.session_state["brand_name_1"])
                b2 = st.text_input("Název Značky 2:", value=st.session_state["brand_name_2"])
            with col_b2:
                b3 = st.text_input("Název Značky 3:", value=st.session_state["brand_name_3"])
                b4 = st.text_input("Název Značky 4:", value=st.session_state["brand_name_4"])
            st.session_state["brand_name_1"] = b1.strip()
            st.session_state["brand_name_2"] = b2.strip()
            st.session_state["brand_name_3"] = b3.strip()
            st.session_state["brand_name_4"] = b4.strip()

            st.markdown("### ✉️ 3. Nastavení reportů")
            email_sefa = st.text_input(t["email_boss_lbl"], value=st.session_state.get("boss_email", "manager@firma.cz"))
            if email_sefa: st.session_state["boss_email"] = email_sefa
            
            st.markdown("### 🏢 4. Aktivace databáze")
            nahrany_soubor = st.file_uploader(t["upload_lbl"])
            if nahrany_soubor is not None:
                df_klienti = zpracuj_a_ulož_soubor(nahrany_soubor)
                if df_klienti is not None:
                    st.session_state["zmena_databaze"] = False
                    st.rerun()
    if df_klienti is None: return
    st.subheader(t["sec_1"])
    col_d1, col_t_h, col_t_m = st.columns(3)
    
    cas_ted_plus_10 = datetime.utcnow() + timedelta(hours=2) + timedelta(minutes=10)
    akt_h, akt_m = cas_ted_plus_10.hour, cas_ted_plus_10.minute
    
    with col_d1: datum_sch = st.date_input(t["date_lbl"], cas_ted_plus_10.date())
    with col_t_h:
        hodiny_list = [f"{i:02d}" for i in range(24)]
        zvolena_hodina = st.selectbox("Hodina:", hodiny_list, index=akt_h)
    with col_t_m:
        minuty_list = ["00", "10", "20", "30", "40", "50"]
        zaok_desitky = int(10 * (akt_m // 10))
        if zaok_desitky >= 60: zaok_desitky = 50
        zvolen_minuta = st.selectbox("Minuta:", minuty_list, index=minuty_list.index(f"{zaok_desitky:02d}"))
    cas_vystup_text = f"{zvolena_hodina}:{zvolen_minuta}"

    st.subheader(t["sec_2"])
    seznam_zakazniku, mapa_surovych_radku = [], {}
    for _, row in df_klienti.iterrows():
        krasny_text = " | ".join([str(row.iloc[i]) for i in range(min(len(row), 6)) if row.iloc[i]])
        seznam_zakazniku.append(krasny_text)
        mapa_surovych_radku[krasny_text] = row.tolist()

    vybrany_box_text = st.selectbox(t["search_hint"], options=seznam_zakazniku, index=None, placeholder=t["select_prompt"])
    st.caption("✍️ Nebo napište jméno ZCELA NOVÉHO klienta ručně (pokud chybí v adresáři):")
    novy_klient_manualni = st.text_input("Zadejte jméno, telefon nebo město nového kontaktu:", value="").strip()

    finalni_klient_vystup = ""
    surovy_radek_pro_zápis = None
    if vybrany_box_text:
        finalni_klient_vystup = vybrany_box_text
        surovy_radek_pro_zápis = mapa_surovych_radku[vybrany_box_text]
        st.success(f"{t['selected_ok']} {finalni_klient_vystup}")
    elif novy_klient_manualni:
        finalni_klient_vystup = f"🆕 {novy_klient_manualni}"
        surovy_radek_pro_zápis = novy_klient_manualni.split("|")
        st.info(f"✨ Nový kontakt: {novy_klient_manualni}")
    st.subheader(t["sec_3"])
    ch_b2b = st.checkbox(t["b2b_lbl"])
    ch_zajem = st.checkbox(t["no_interest"])
    st.caption(t["samples_lbl"])
    
    aktivni_znacky_seznam = []
    for klicek in ["brand_name_1", "brand_name_2", "brand_name_3", "brand_name_4"]:
        if st.session_state[klicek]: aktivni_znacky_seznam.append(st.session_state[klicek])
            
    zvolene_v_checkboxech = {}
    if aktivni_znacky_seznam:
        mobilni_sloupciky = st.columns(len(aktivni_znacky_seznam))
        for i, jmeno_znacky in enumerate(aktivni_znacky_seznam):
            with mobilni_sloupciky[i]: zvolene_v_checkboxech[jmeno_znacky] = st.checkbox(jmeno_znacky, key=f"chk_dyn_{jmeno_znacky}")
                
    zapisane_slevy = {}
    for jmeno_znacky, zaskrtnuto in zvolene_v_checkboxech.items():
        if zaskrtnuto: zapisane_slevy[jmeno_znacky] = st.text_input(f"Sleva {jmeno_znacky} (%):", value="", key=f"input_dyn_sl_{jmeno_znacky}")
        
    txt_konkurence = st.text_input(t["competitor_lbl"], value="")
    txt_potencial = st.text_input(t["potential_lbl"], value="")
    st.subheader(t["sec_4"])
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        desitkove_intervaly = ["10", "20", "30", "40", "50", "60", "70", "80", "90", "100", "110", "120"]
        txt_trvani = st.selectbox(t["duration_lbl"], desitkove_intervaly, index=0)
        ch_ozvat = st.checkbox(t["remind_check"])
        dt_ozvat = st.date_input(t["remind_date"], (datetime.utcnow() + timedelta(hours=2)).date()) if ch_ozvat else None
    with col_t2: txt_poznamka = st.text_area(t["note_lbl"], height=115)
    st.write("---")
    if st.button(t["btn_save"], use_container_width=True):
        if not finalni_klient_vystup: st.error("❌ Vyberte klienta ze seznamu!")
        else:
            sit_seznam = []
            if ch_b2b: sit_seznam.append("Bude zaslán přístup na B2B")
            if ch_zajem: sit_seznam.append("Nemá zájem - bere od jiných")
            vybrane_v_akci = [z for z, c in zvolene_v_checkboxech.items() if c]
            if vybrane_v_akci: sit_seznam.insert(0, f"Předvedeny vzorky ({', '.join(vybrane_v_akci)})")
            
            slevy_vystup_list = [f"{znacka}: {hodnota} %" for znacka, hodnota in zapisane_slevy.items() if hodnota.strip()]
            slevy_objekt = {
                "situace": ", ".join(sit_seznam) if sit_seznam else "Žádná specifická situace",
                "sleva": ", ".join(slevy_vystup_list) if slevy_vystup_list else "Není",
                "konkurence": txt_konkurence if txt_konkurence else "Nezadáno", "potencial": f"{txt_potencial} %" if txt_potencial else "Nezadáno"
            }
            if zapis_zaznam_na_disk(finalni_klient_vystup, datum_sch, cas_vystup_text, txt_trvani, dt_ozvat, slevy_objekt, txt_poznamka, jazyk, surovy_radek_pro_zápis):
                st.success(t["save_success"])
                st.rerun()

    st.write("---")
    st.subheader("📋 Deník mých návštěv")
    if os.path.exists(HISTORIE_SOUBOR):
        try:
            df_hist = pd.read_csv(HISTORIE_SOUBOR, dtype=str)
            df_zobrazeni = df_hist.copy()
            df_zobrazeni["skutecny_index"] = df_zobrazeni.index
            
            def parsuj_kalendarne(row_item):
                try: return datetime.strptime(f"{row_item['Datum']} {row_item['Čas']}", "%d.%m.%Y %H:%M")
                except: return datetime.min
            
            df_zobrazeni["Timestamp_Serazeni"] = df_zobrazeni.apply(parsuj_kalendarne, axis=1)
            df_sorted_calendar = df_zobrazeni.sort_values(by="Timestamp_Serazeni", ascending=False)
            
            if "RawText_Zaloha" in df_sorted_calendar.columns:
                df_sorted_calendar = df_sorted_calendar.drop(columns=["RawText_Zaloha", "Timestamp_Serazeni"])
                
            for _, radek_historie in df_sorted_calendar.iterrows():
                puvodni_radek_id = int(radek_historie["skutecny_index"])
                with st.container(border=True):
                    st.markdown(f"📅 **{radek_historie['Datum']} {radek_historie['Čas']}** | 🏢 **{radek_historie['Klient']}**")
                    st.markdown(f"📝 **Poznámka:** {radek_historie['Poznámka']}")
                    
                    pojistka_key = f"confirm_del_state_{puvodni_radek_id}"
                    if pojistka_key not in st.session_state: st.session_state[pojistka_key] = False
                        
                    if not st.session_state[pojistka_key]:
                        if st.button(f"🗑️ Smazat tento zápis", key=f"del_row_hist_init_{puvodni_radek_id}", use_container_width=True):
                            st.session_state[pojistka_key] = True
                            st.rerun()
                    else:
                        st.warning("⚠️ Opravdu smazat? Tuto akci nelze vrátit zpět.")
                        col_poj1, col_poj2 = st.columns(2)
                        with col_poj1:
                            if st.button("🟢 ANO, SMAZAT", key=f"del_row_hist_{puvodni_radek_id}_yes", use_container_width=True):
                                df_upraveny_hist = df_hist.drop(df_hist.index[puvodni_radek_id])
                                df_upraveny_hist.to_csv(HISTORIE_SOUBOR, index=False, encoding="utf-8")
                                st.session_state[pojistka_key] = False
                                st.success("Zápis smazán!")
                                st.rerun()
                        with col_poj2:
                            if st.button("⚪ ZPĚT", key=f"del_row_hist_{puvodni_radek_id}_no", use_container_width=True):
                                st.session_state[pojistka_key] = False
                                st.rerun()
            
            st.write("")
            kompletni_text_mailu = "\n".join(df_hist["RawText_Zaloha"].tolist()) if "RawText_Zaloha" in df_hist.columns else ""
            mail_odkaz = f"mailto:{st.session_state.get('boss_email', '')}?subject={urllib.parse.quote('RouteReport')}&body={urllib.parse.quote(kompletni_text_mailu)}"
            st.markdown(f'<a href="{mail_odkaz}" target="_blank"><button style="width:100%; height:52px; background-color:#1E88E5; color:white; border:none; border-radius:5px; font-weight:bold;">✉️ ODESLAT REPORT MANAŽEROVI</button></a>', unsafe_allow_html=True)
        except: pass
    if os.path.exists(HISTORIE_SOUBOR):
        try:
            df_buffer_h = pd.read_csv(HISTORIE_SOUBOR, dtype=str)
            df_buffer_u = pd.read_csv(UKOLY_SOUBOR, dtype=str) if os.path.exists(UKOLY_SOUBOR) else pd.DataFrame()
            string_io_vystup = io.StringIO()
            df_buffer_h.to_csv(string_io_vystup, index=False, encoding="utf-8")
            string_io_vystup.write("===UKOLY_SEPARATOR===\n")
            if not df_buffer_u.empty: df_buffer_u.to_csv(string_io_vystup, index=False, encoding="utf-8")
            csv_spojena_data = string_io_vystup.getvalue()
            st.download_button(label="📥 STÁHNOUT ZÁLOHU DENÍKU I ÚKOLŮ (.CSV)", data=csv_spojena_data, file_name="routereport_zaloha.csv", mime="text/csv", use_container_width=True)
        except: pass
            
    with st.expander("📤 Obnovit starší deník i úkoly ze záložního souboru (.csv)"):
        st.markdown("<small>💡 <i>Tip: Pokud přecházíte na nový počítač, zde můžete jedním kliknutím nahrát zpět celou svou historii schůzek i vnitřní připomínky.</i></small>", unsafe_allow_html=True)
        soubor_zalohy_spodní = st.file_uploader("Vyberte stažený soubor routereport_zaloha.csv:", key="bottom_backup_uploader_clean")
        if soubor_zalohy_spodní is not None:
            if obnov_data_ze_zalohy_backend(soubor_zalohy_spodní):
                # 🟢 CHYBA 1 OPRAVENA: Okamžitý automatický restart – záloha i úkoly se objeví ihned bez klikání na aktualizaci stránky!
                st.rerun()

    st.write("")
    if os.path.exists(HISTORIE_SOUBOR):
        if "confirm_wipe_out_all" not in st.session_state: st.session_state["confirm_wipe_out_all"] = False
        if not st.session_state["confirm_wipe_out_all"]:
            if st.button("🚨 VYMAZAT KOMPLETNĚ CELÝ DENÍK NÁVŠTĚV", use_container_width=True):
                st.session_state["confirm_wipe_out_all"] = True
                st.rerun()
        else:
            st.error("⚠️ OPRAVDU CHCETE VYMAZAT HISTORII VŠECH ZÁPISŮ? (VAŠE VNITŘNÍ PŘIPOMÍNKY DO BUDOUCNA ZŮSTANOU BEZPEČNĚ NATVRDO ZACHOVÁNY)")
            c_w1, c_w2 = st.columns(2)
            with c_w1:
                if st.button("🟢 ANO, VYMAZAT DENÍK", use_container_width=True, key="btn_wipe_yes"):
                    if os.path.exists(HISTORIE_SOUBOR): os.remove(HISTORIE_SOUBOR)
                    if os.path.exists(EXPORT_FILE): os.remove(EXPORT_FILE)
                    st.session_state["confirm_wipe_out_all"] = False
                    st.rerun()
            with c_w2:
                if st.button("⚪ ZPĚT", use_container_width=True, key="btn_wipe_no"):
                    st.session_state["confirm_wipe_out_all"] = False
                    st.rerun()

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
                    t_id = row_u["TaskID"] if "TaskID" in row_u and pd.notna(row_u["TaskID"]) else f"OLD_{idx}"
                    
                    with st.container(border=True):
                        cisty_vzhled_klienta = str(row_u['Klient']).replace("nan", "").replace("|", " ").replace("  ", " ").strip()
                        st.markdown(f"**{status_badge}** | 📅 {row_u['Termín']} | 🏢 **{cisty_vzhled_klienta}**")
                        st.markdown(f"📝 Důvod: {row_u['Důvod (Kvůli čemu)']}")
                        tel_val = str(row_u.get('Telefon', '')).strip().replace("nan", "")
                        mail_val = str(row_u.get('Email', '')).strip().replace("nan", "")
                        
                        col_c1, col_c2 = st.columns(2)
                        with col_c1:
                            if tel_val and tel_val != "Nezadáno" and tel_val != "": st.markdown(f'<a href="tel:{tel_val}" style="text-decoration:none;"><button style="width:100%; height:42px; background-color:#2E7D32; color:white; border:none; border-radius:5px; font-weight:bold; font-size:12px; cursor:pointer;">📞 ZAVOLAT: {tel_val}</button></a>', unsafe_allow_html=True)
                            else: st.markdown('<a href="tel:" style="text-decoration:none;"><button style="width:100%; height:42px; background-color:#555555; color:white; border:none; border-radius:5px; font-weight:bold; font-size:12px; cursor:pointer;">📞 OTEVŘÍT TELEFON</button></a>', unsafe_allow_html=True)
                        with col_c2:
                            if mail_val and mail_val != "Nezadáno" and mail_val != "": st.markdown(f'<a href="mailto:{mail_val}" style="text-decoration:none;"><button style="width:100%; height:42px; background-color:#1565C0; color:white; border:none; border-radius:5px; font-weight:bold; font-size:12px; cursor:pointer;">✉️ NAPÍSAT E-MAIL</button></a>', unsafe_allow_html=True)
                            else: st.markdown('<a href="mailto:" style="text-decoration:none;"><button style="width:100%; height:42px; background-color:#555555; color:white; border:none; border-radius:5px; font-weight:bold; font-size:12px; cursor:pointer;">✉️ OTEVŘÍT E-MAIL</button></a>', unsafe_allow_html=True)
                        
                        st.write("")
                        # 🟢 CHYBA 2 OPRAVENA: Čistá dvoukroková pojistka přesně podle vašeho zadání! Tlačítko se nemaže samo do sebe.
                        pojistka_u_key = f"confirm_task_wipe_{t_id}"
                        if pojistka_u_key not in st.session_state: st.session_state[pojistka_u_key] = False
                        
                        if not st.session_state[pojistka_u_key]:
                            if st.button("🗑️ Vyřídit úkol", key=f"init_del_task_{t_id}", use_container_width=True):
                                st.session_state[pojistka_u_key] = True
                                st.rerun()
                        else:
                            st.warning("⚠️ Opravdu chcete vyřídit?")
                            col_tsk1, col_tsk2 = st.columns(2)
                            with col_tsk1:
                                if st.button("🟢 ANO, VYMAZAT", key=f"yes_del_task_{t_id}", use_container_width=True):
                                    if "TaskID" in df_ukoly.columns: df_upravene_ukoly = df_ukoly[df_ukoly["TaskID"] != t_id]
                                    else: df_upravene_ukoly = df_ukoly.drop(df_ukoly.index[idx])
                                    df_upravene_ukoly.to_csv(UKOLY_SOUBOR, index=False, encoding="utf-8")
                                    st.session_state[pojistka_u_key] = False
                                    st.rerun()
                            with col_tsk2:
                                if st.button("⚪ ZPĚT", key=f"no_del_task_{t_id}", use_container_width=True):
                                    st.session_state[pojistka_u_key] = False
                                    st.rerun()
            else: st.caption("Žádné připomínky.")
        except: st.caption("Žádné připomínky.")
    else: st.caption("Žádné připomínky.")

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
