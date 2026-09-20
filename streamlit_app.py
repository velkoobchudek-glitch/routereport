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
        "cfg_sec": "⚙️ Nastavení adresáře zákazníků (CSV)",
        "cfg_info": "Nahrajte soubor CSV se zákazníky a zadejte e-mail šéfa.",
        "upload_lbl": "Vyberte soubor s klienty (pouze CSV):",
        "email_boss_lbl": "E-mailová adresa manažera / šéfa:",
        "db_loaded_ok": "✅ Adresář zákazníků i e-mail jsou bezpečně uloženy.",
        "db_change_btn": "🔄 Aktualizovat adresář klientů / Změnit e-mail šéfa",
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
def zapis_zaznam_na_disk(klient_vystup, datum, cas_text, trvani, ozvat_se, slevy_data, poznamka, jazyk):
    oddelovac = "=" * 45
    t = LANG[jazyk]
    
    ciste_jmeno = str(klient_vystup).replace(" | ", " ").strip()
    
    # 🟢 AKTUALIZACE: Prohledáme text řádku a vytáhneme telefon i e-mail z originálních sloupců
    cisty_tel, cisty_mail = "", ""
    for prvek in ciste_jmeno.split():
        if "@" in prvek: 
            cisty_mail = prvek
        else:
            ciste_cislo = prvek.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
            if ciste_cislo.replace("+", "").isdigit() and len(ciste_cislo.replace("+", "")) >= 9:
                cisty_tel = ciste_cislo
            
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
            # Uložíme telefon i e-mail do vnitřní databáze úkolů, aby je ČÁST 11 mohla hned prokliknout
            novy_ukol = {
                "Termín": ozvat_se.strftime('%d.%m.%Y'), 
                "Klient": ciste_jmeno[:120], 
                "Telefon": cisty_tel if cisty_tel else "Nezadáno", 
                "Email": cisty_mail if cisty_mail else "Nezadáno", 
                "Důvod (Kvůli čemu)": f"Slevy: {slevy_data['sleva']}. {poznamka}"
            }
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
    seznam_zakazniku = []
    for _, row in df_klienti.iterrows():
        krasny_text = " | ".join([str(row.iloc[i]) for i in range(min(len(row), 6)) if row.iloc[i]])
        seznam_zakazniku.append(krasny_text)

    vybrany_box_text = st.selectbox(t["search_hint"], options=seznam_zakazniku, index=None, placeholder=t["select_prompt"])
    st.caption("✍️ Nebo napište jméno ZCELA NOVÉHO klienta ručně (pokud chybí v adresáři):")
    novy_klient_manualni = st.text_input("Zadejte jméno, telefon nebo město nového kontaktu:", value="", placeholder="Např. Jan Nečas | +420777123456").strip()

    finalni_klient_vystup = ""
    if vybrany_box_text:
        finalni_klient_vystup = vybrany_box_text
        st.success(f"{t['selected_ok']} {finalni_klient_vystup}")
    elif novy_klient_manualni:
        finalni_klient_vystup = f"🆕 {novy_klient_manualni}"
        st.info(f"✨ Nový kontakt: {novy_klient_manualni}")
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
        if not finalni_klient_vystup: st.error("❌ Vyberte klienta ze seznamu!")
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
            if zapis_zaznam_na_disk(finalni_klient_vystup, datum_sch, cas_vystup_text, txt_trvani, dt_ozvat, slevy_objekt, txt_poznamka, jazyk):
                st.success(t["save_success"])
                st.rerun()

    st.write("---")
    st.subheader("📋 Deník mých návštěv")
    if os.path.exists(HISTORIE_SOUBOR):
        try:
            df_hist = pd.read_csv(HISTORIE_SOUBOR, dtype=str)
            df_zobrazeni = df_hist.copy()
            df_zobrazeni["skutecny_index"] = df_zobrazeni.index
            df_inverted = df_zobrazeni.iloc[::-1]
            
            for _, radek_historie in df_inverted.iterrows():
                puvodni_radek_id = int(radek_historie["skutecny_index"])
                with st.container(border=True):
                    st.markdown(f"📅 **{radek_historie['Datum']} {radek_historie['Čas']}** | 🏢 **{radek_historie['Klient']}**")
                    st.markdown(f"📝 **Poznámka:** {radek_historie['Poznámka']}")
                    if st.button(f"🗑️ Smazat tento zápis", key=f"del_row_hist_{puvodni_radek_id}", use_container_width=True):
                        df_upraveny_hist = df_hist.drop(df_hist.index[puvodni_radek_id])
                        df_upraveny_hist.to_csv(HISTORIE_SOUBOR, index=False, encoding="utf-8")
                        st.success("Zápis smazán!")
                        st.rerun()
            
            st.write("")
            kompletni_text_mailu = "\n".join(df_hist["RawText_Zaloha"].tolist()) if "RawText_Zaloha" in df_hist.columns else ""
            mail_odkaz = f"mailto:{st.session_state.get('boss_email', '')}?subject={urllib.parse.quote('RouteReport')}&body={urllib.parse.quote(kompletni_text_mailu)}"
            st.markdown(f'<a href="{mail_odkaz}" target="_blank"><button style="width:100%; height:52px; background-color:#1E88E5; color:white; border:none; border-radius:5px; font-weight:bold;">✉️ ODESLAT REPORT MANAŽEROVI</button></a>', unsafe_allow_html=True)
        except: pass
    if os.path.exists(HISTORIE_SOUBOR):
        try:
            df_hist_download = pd.read_csv(HISTORIE_SOUBOR, dtype=str)
            csv_data_data = df_hist_download.to_csv(index=False, encoding="utf-8")
            st.download_button(label="📥 STÁHNOUT ZÁLOHU DENÍKU (.CSV)", data=csv_data_data, file_name="routereport_zaloha.csv", mime="text/csv", use_container_width=True)
        except: pass
            
    with st.expander("📤 Obnovit deník ze starší zálohy (.csv)"):
        st.markdown("<small>💡 <i>Tip: V telefonu soubor hledejte ve složce <b>Stažené soubory (Downloads)</b> pod názvem <b>routereport_zaloha.csv</b>.</i></small>", unsafe_allow_html=True)
        soubor_zalohy = st.file_uploader("Vyberte stažený soubor zálohy:", type=["csv"])
        if soubor_zalohy is not None:
            try:
                bytes_z = soubor_zalohy.read()
                text_z = bytes_z.decode("utf-8", errors="ignore")
                df_import_zaloha = pd.read_csv(io.StringIO(text_z), dtype=str)
                df_import_zaloha.to_csv(HISTORIE_SOUBOR, index=False, encoding="utf-8")
                st.success("✅ Záloha nahrána! Restartuji...")
                st.rerun()
            except Exception as e: st.error(f"Chyba: {e}")

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
                        # 🟢 VYČIŠTĚNÍ DISPLEJE: Odstraníme "nan" a ošklivé znaky rovnou z textu karty
                        cisty_vzhled_klienta = str(row_u['Klient']).replace("nan", "").replace("|", " ").replace("  ", " ").strip()
                        st.markdown(f"**{status_badge}** | 📅 {row_u['Termín']} | 🏢 **{cisty_vzhled_klienta}**")
                        st.markdown(f"📝 Důvod: {row_u['Důvod (Kvůli čemu)']}")
                        
                        # 🟢 HLOUBKOVÝ SRENING: Najde jakékoliv telefonní číslo ukryté uvnitř celé karty
                        cely_balik_textu = str(row_u['Klient']) + " " + str(row_u.get('Telefon', '')) + " " + str(row_u.get('Email', ''))
                        cely_balik_textu = cely_balik_textu.replace("nan", "").replace("|", " ")
                        
                        nalezeny_tel = ""
                        nalezeny_mail = ""
                        for slovo in cely_balik_textu.split():
                            if "@" in slovo:
                                nalezeny_mail = slovo.strip(".,()[]{}")
                            else:
                                ciste_slovo = slovo.replace(" ", "").replace("-", "").replace("(", "").replace(")", "").strip(".,()[]{}|")
                                if ciste_slovo.replace("+", "").isdigit() and len(ciste_slovo.replace("+", "")) >= 9:
                                    nalezeny_tel = ciste_slovo
                        
                        col_c1, col_c2 = st.columns(2)
                        with col_c1:
                            if nalezeny_tel:
                                st.markdown(f'<a href="tel:{nalezeny_tel}" style="text-decoration:none;"><button style="width:100%; height:42px; background-color:#2E7D32; color:white; border:none; border-radius:5px; font-weight:bold; font-size:12px; cursor:pointer;">📞 ZAVOLAT: {nalezeny_tel}</button></a>', unsafe_allow_html=True)
                            else:
                                st.markdown('<a href="tel:" style="text-decoration:none;"><button style="width:100%; height:42px; background-color:#555555; color:white; border:none; border-radius:5px; font-weight:bold; font-size:12px; cursor:pointer;">📞 OTEVŘÍT TELEFON</button></a>', unsafe_allow_html=True)
                        with col_c2:
                            if nalezeny_mail:
                                st.markdown(f'<a href="mailto:{nalezeny_mail}" style="text-decoration:none;"><button style="width:100%; height:42px; background-color:#1565C0; color:white; border:none; border-radius:5px; font-weight:bold; font-size:12px; cursor:pointer;">✉️ E-MAIL</button></a>', unsafe_allow_html=True)
                            else:
                                st.markdown('<a href="mailto:" style="text-decoration:none;"><button style="width:100%; height:42px; background-color:#555555; color:white; border:none; border-radius:5px; font-weight:bold; font-size:12px; cursor:pointer;">✉️ OTEVŘÍT E-MAIL</button></a>', unsafe_allow_html=True)
                        
                        st.write("")
                        if st.button("✅ Vyřízeno", key=f"del_{idx}", use_container_width=True):
                            df_ukoly.drop(df_ukoly.index[idx]).to_csv(UKOLY_SOUBOR, index=False, encoding="utf-8")
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
