# -*- coding: utf-8 -*-
import os
import csv
import sys
import io
import urllib.parse
import unicodedata
from datetime import datetime

# 🟢 KLÍČOVÝ UPGRADE: Vynutíme instalaci pytz přímo v kódu, aby Streamlit uměl přesný český čas
try:
    import pytz
except ImportError:
    import subprocess
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pytz"])
        import pytz
    except Exception as e:
        pass

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
UKOLY_SOUBOR = "crm_ukoly_kalendar.csv"
LANG = {
    "CS": {
        "title": "📱 RouteReport - Poznámky z terénu",
        "cfg_sec": "⚙️ Nastavení databáze zákazníků a e-mailu",
        "cfg_info": "Nahrajte soubor CSV se zákazníky a zadejte e-mail šéfa. Aplikace si vše trvale zapamatuje.",
        "upload_lbl": "Vyberte soubor (pouze CSV):",
        "email_boss_lbl": "E-mailová adresa manažera / šéfa (kam se posílá info):",
        "db_loaded_ok": "✅ Adresář zákazníků i e-mail jsou bezpečně uloženy v mobilu.",
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
        "remind_check": "🔔 Naplánovat termín příštího kontaktu / ozvání (Vnitřní připomínka)",
        "remind_date": "Kdy se ozvat znovu:",
        "btn_save": "💾 ULOŽIT INFO O NÁVŠTĚVĚ",
        "save_success": "✅ Info o návštěvě úspěšně uloženo do deníku na pozadí!",
        "copy_title": "📋 Text ke zkopírování (pokud potřebujete):",
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
        "title": "📱 RouteReport - Field Notes",
        "cfg_sec": "⚙️ Customer Database & Email Settings",
        "cfg_info": "Upload a CSV file with your customers and enter the manager's email. The app will remember it.",
        "upload_lbl": "Select database file (CSV only):",
        "email_boss_lbl": "Manager / Boss Email Address (where info is sent):",
        "db_loaded_ok": "✅ Customer database and email are permanently saved in your mobile.",
        "db_change_btn": "🔄 Update Database / Change Email",
        "sec_1": "1. Date, Time and Duration of the Visit",
        "date_lbl": "Date:",
        "time_lbl": "Visit Time (Hour / Minute):",
        "duration_lbl": "Visit Duration:",
        "sec_2": "2. Search and Select Client",
        "search_hint": "Tap and start typing name or city...",
        "select_prompt": "-- Start typing client name or city --",
        "selected_ok": "🤝 Selected for log:",
        "no_client": "❌ No client matches your search.",
        "sec_3": "3. Field Situations and Discounts",
        "b2b_lbl": "B2B portal login will be sent",
        "no_interest": "No interest - buys from competitors",
        "samples_lbl": "Samples presented for brands:",
        "discount_lbl": "Promised discount on main brand (%):",
        "competitor_lbl": "Main competitor in store:",
        "potential_lbl": "Store purchase potential (%):",
        "sec_4": "4. Visit Minutes and Notes",
        "note_lbl": "Write visit notes or summary:",
        "remind_check": "Schedule follow-up / Next contact (Internal Reminder)",
        "remind_date": "When to call again:",
        "btn_save": "💾 SAVE VISIT INFO",
        "save_success": "✅ Visit info successfully saved to log on background!",
        "copy_title": "📋 Text to copy (if needed):",
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
        st.error(f"Chyba zpracování CSV souboru: {e}")
        return None

def nacti_trvale_ulozeny_adresar():
    if os.path.exists(ULOZENY_ADRESAR_FILE):
        try:
            return pd.read_csv(ULOZENY_ADRESAR_FILE, dtype=str)
        except:
            pass
    return None
def zapis_zaznam_na_disk(klient_radek, datum, cas_text, trvani, ozvat_se, slevy_data, poznamka, jazyk):
    oddelovac = "=" * 45
    t = LANG[jazyk]
    klient_vystup = " | ".join([str(x) for x in klient_radek[:6] if x])
    
    ciste_jmeno = "Klient"
    if len(klient_radek) > 0:
        ciste_jmeno = str(klient_radek).strip()
    
    cisty_tel = ""
    cisty_mail = ""
    for policko in [str(x).strip() for x in klient_radek]:
        if "@" in policko:
            cisty_mail = policko
        elif policko.isdigit() and len(policko) >= 9:
            cisty_tel = policko
        elif ("+" in policko) and len(policko) >= 10:
            cisty_tel = policko
            
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
        with open(EXPORT_FILE, "a", encoding="utf-8") as f:
            f.write(blok_textu)
            
        novy_radek = {
            "Datum": datum.strftime('%d.%m.%Y'),
            "Čas": cas_text,
            "Klient": klient_vystup,
            "Trvání (min)": trvani,
            "Situace": slevy_data['situace'],
            "Slevy Značek": slevy_data['sleva'],
            "Konkurence": slevy_data['konkurence'],
            "Potenciál": slevy_data['potencial'],
            "Poznámka": poznamka if poznamka else "",
            "RawText_Zaloha": blok_textu
        }
        df_novy = pd.DataFrame([novy_radek])
        if os.path.exists(HISTORIE_SOUBOR):
            df_novy.to_csv(HISTORIE_SOUBOR, mode='a', header=False, index=False, encoding="utf-8")
        else:
            df_novy.to_csv(HISTORIE_SOUBOR, mode='w', header=True, index=False, encoding="utf-8")
            
        if ozvat_se:
            duvod_kontaktu = f"Slevy: {slevy_data['sleva']}. Poznámka: {poznamka if poznamka else 'Kontrola stavu.'}"
            novy_ukol = {
                "Termín": ozvat_se.strftime('%d.%m.%Y'),
                "Klient": ciste_jmeno,
                "Telefon": cisty_tel,
                "Email": cisty_mail,
                "Důvod (Kvůli čemu)": duvod_kontaktu
            }
            df_ukol = pd.DataFrame([novy_ukol])
            if os.path.exists(UKOLY_SOUBOR):
                df_ukol.to_csv(UKOLY_SOUBOR, mode='a', header=False, index=False, encoding="utf-8")
            else:
                df_ukol.to_csv(UKOLY_SOUBOR, mode='w', header=True, index=False, encoding="utf-8")
            
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
    
    if os.path.exists(UKOLY_SOUBOR):
        try:
            df_kontrol_u = pd.read_csv(UKOLY_SOUBOR, dtype=str)
            if not df_kontrol_u.empty:
                # Načtení dnešního data v české časové zóně
                try:
                    cz_tz = pytz.timezone('Europe/Prague')
                    dnes_str = datetime.now(cz_tz).strftime('%d.%m.%Y')
                except:
                    dnes_str = datetime.now().strftime('%d.%m.%Y')
                    
                shody_dnes = df_kontrol_u[df_kontrol_u["Termín"] == dnes_str]
                
                if len(shody_dnes) > 0 and "popup_odkliknuto" not in st.session_state:
                    @st.dialog("🔔 DNEŠNÍ URGENTNÍ ÚKOLY")
                    def ranni_popup_okno():
                        st.error(f"⚠️ Pozor! Dnes máte naplánované {len(shody_dnes)} úkoly:")
                        for _, r_u in shody_dnes.iterrows():
                            st.markdown(f"🏢 **Klient:** {r_u['Klient']}")
                            st.markdown(f"📝 **Úkol:** {r_u['Důvod (Kvůli čemu)']}")
                            st.write("---")
                        if st.button("Rozumím, jdu pracovat 👍", use_container_width=True):
                            st.session_state["popup_odkliknuto"] = True
                            st.rerun()
                    ranni_popup_okno()
        except:
            pass
            
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
                
            nahrany_soubor = st.file_uploader(t["upload_lbl"], type=["csv", "txt"])
            if nahrany_soubor is not None:
                df_klienti = zpracuj_a_ulož_soubor(nahrany_soubor)
                if df_klienti is not None:
                    st.session_state["zmena_databaze"] = False
                    st.success("👍 Importováno!")
                    st.rerun()

    if df_klienti is None:
        return
    # Sekce 1: Čas se automaticky načte podle reálného českého času v mobilu
    st.subheader(t["sec_1"])
    col_d1, col_t_h, col_t_m = st.columns(3)
    
    # 🟢 VYNUCENÍ ČESKÉHO ČASU (Evropa/Praha)
    try:
        cz_tz = pytz.timezone('Europe/Prague')
        cas_v_cr = datetime.now(cz_tz)
        aktualni_hodina_mobil = cas_v_cr.hour
        aktualni_minuta_mobil = cas_v_cr.minute
        dnesni_datum_cr = cas_v_cr.date()
    except:
        aktualni_hodina_mobil = datetime.now().hour
        aktualni_minuta_mobil = datetime.now().minute
        dnesni_datum_cr = datetime.now().date()
        
    # Zaokrouhlení minut na nejbližší pětku pro rozevírací seznam
    zaokrouhlena_minuta = int(5 * round(aktualni_minuta_mobil / 5))
    if zaokrouhlena_minuta >= 60: zaokrouhlena_minuta = 55

    with col_d1:
        datum_sch = st.date_input(t["date_lbl"], dnesni_datum_cr)
    with col_t_h:
        hodiny_list = [f"{i:02d}" for i in range(24)]
        zvolena_hodina = st.selectbox("Hodina:", hodiny_list, index=aktualni_hodina_mobil)
    with col_t_m:
        minuty_list = [f"{i:02d}" for i in range(0, 60, 5)]
        zvolen_minuta = st.selectbox("Minuta:", minuty_list, index=minuty_list.index(f"{zaokrouhlena_minuta:02d}"))
        
    cas_vystup_text = f"{zvolena_hodina}:{zvolen_minuta}"

    # Sekce 2: Hledání a výběr klienta (Rozšířeno na 6 polí)
    st.subheader(t["sec_2"])
    
    seznam_zakazniku = []
    mapovani_zaznamu = {}
    
    for _, row in df_klienti.iterrows():
        krasny_text = " | ".join([str(row.iloc[i]) for i in range(min(len(row), 6)) if row.iloc[i]])
        seznam_zakazniku.append(krasny_text)
        mapovani_zaznamu[krasny_text] = row.tolist()

    vybrany_box_text = st.selectbox(
        t["search_hint"],
        options=seznam_zakazniku,
        index=None,
        placeholder=t["select_prompt"]
    )
    
    vybrany_klient = None
    if vybrany_box_text and vybrany_box_text in mapovani_zaznamu:
        vybrany_klient = mapovani_zaznamu[vybrany_box_text]
        st.success(f"{t['selected_ok']} {vybrany_box_text}")
    # Sekce 3: Situace a slevy značek
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
    if m_bbb: zapisane_slevy["BBB"] = st.text_input("Slíbená sleva na BBB (%):", value="", key="sleva_bbb_input")
    if m_cyclon: zapisane_slevy["CYCLON"] = st.text_input("Slíbená sleva na CYCLON (%):", value="", key="sleva_cyclon_input")
    if m_basil: zapisane_slevy["BASIL"] = st.text_input("Slíbená sleva na BASIL (%):", value="", key="sleva_basil_input")
    if m_rozzo: zapisane_slevy["ROZZO"] = st.text_input("Slíbená sleva na ROZZO (%):", value="", key="sleva_rozzo_input")
        
    st.write("") 
    txt_konkurence = st.text_input(t["competitor_lbl"], value="")
    txt_potencial = st.text_input(t["potential_lbl"], value="")

    st.subheader(t["sec_4"])
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        skoky_trvani = [str(i) for i in range(5, 125, 5)]
        txt_trvani = st.selectbox(t["duration_lbl"], skoky_trvani, index=5)
        st.write("") 
        ch_ozvat = st.checkbox(t["remind_check"])
        
        try:
            cz_tz = pytz.timezone('Europe/Prague')
            def_remind_date = datetime.now(cz_tz).date()
        except:
            def_remind_date = datetime.now().date()
            
        dt_ozvat = st.date_input(t["remind_date"], def_remind_date) if ch_ozvat else None
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
            if zvolene_znacky: sit_seznam.insert(0, f"Předvedeny vzorky ({', '.join(zvolene_znacky)})")
            
            slevy_vystup_list = []
            for znacka, hodnota in zapisane_slevy.items():
                if hodnota.strip(): slevy_vystup_list.append(f"{znacka}: {hodnota} %")
            sleva_string = ", ".join(slevy_vystup_list) if slevy_vystup_list else "Není"
            
            slevy_objekt = {
                "situace": ", ".join(sit_seznam) if sit_seznam else "Žádná specifická situace",
                "sleva": sleva_string,
                "konkurence": txt_konkurence if txt_konkurence else "Nezadáno",
                "potencial": f"{txt_potencial} %" if txt_potencial else "Nezadáno"
            }
            
            vystupni_blok = zapis_zaznam_na_disk(vybrany_klient, datum_sch, cas_vystup_text, txt_trvani, dt_ozvat, slevy_objekt, txt_poznamka, jazyk)
            if vystupni_blok:
                st.success(t["save_success"])
                st.rerun()

    st.write("---")
    hist_title = "📋 Deník mých návštěv" if jazyk == "CS" else "📋 My Visit Log"
    st.subheader(hist_title)
    
    if os.path.exists(HISTORIE_SOUBOR):
        try:
            df_hist = pd.read_csv(HISTORIE_SOUBOR, dtype=str)
            df_zobrazeni = df_hist.copy()
            df_zobrazeni.index = df_zobrazeni.index + 1
            if "RawText_Zaloha" in df_zobrazeni.columns: df_zobrazeni = df_zobrazeni.drop(columns=["RawText_Zaloha"])
            df_zobrazeni = df_zobrazeni.iloc[::-1]
            st.dataframe(df_zobrazeni, use_container_width=True)
            
            st.write("")
            with st.container():
                send_sec_title = "✉️ Odeslání nashromážděných poznámek:" if jazyk == "CS" else "✉️ Send Collected Visit Notes:"
                st.subheader(send_sec_title)
                datumy_v_tabulce = df_hist["Datum"].tolist()
                od_kdy = datumy_v_tabulce if datumy_v_tabulce else datetime.now().strftime('%d.%m.%Y')
                do_kdy = datumy_v_tabulce[-1] if datumy_v_tabulce else datetime.now().strftime('%d.%m.%Y')
                
                kompletni_text_mailu = ""
                if "RawText_Zaloha" in df_hist.columns: kompletni_text_mailu = "\n".join(df_hist["RawText_Zaloha"].tolist())
                text_pro_url = urllib.parse.quote(kompletni_text_mailu)
                mail_subject = f"RouteReport: Info o návštěvách ({od_kdy} - {do_kdy})" if jazyk == "CS" else f"RouteReport: Visit Notes ({od_kdy} - {do_kdy})"
                predmet_pro_url = urllib.parse.quote(mail_subject)
                boss_email_adr = st.session_state.get("boss_email", "")
                
                btn_label = f"✉️ ODESLAT INFO O NÁVŠTĚVÁCH MANAŽEROVI ({od_kdy} - {do_kdy})" if jazyk == "CS" else f"✉️ SEND VISIT NOTES TO MANAGER ({od_kdy} - {do_kdy})"
                mail_odkaz = f"mailto:{boss_email_adr}?subject={predmet_pro_url}&body={text_pro_url}"
                st.markdown(f'<a href="{mail_odkaz}" target="_blank" style="text-decoration:none;"><button style="width:100%; height:52px; background-color:#1E88E5; color:white; border:none; border-radius:5px; font-weight:bold; font-size:14px; cursor:pointer;">{btn_label}</button></a>', unsafe_allow_html=True)
        except Exception as e:
            st.caption(f"Ready / Připraveno. ({e})")
    # Vnitřní nezávislý kalendář přímo na obrazovce
    st.write("---")
    tasks_title = "📅 Moje nadcházející úkoly (Připomínky)"
    st.subheader(tasks_title)
    if os.path.exists(UKOLY_SOUBOR):
        try:
            df_ukoly = pd.read_csv(UKOLY_SOUBOR, dtype=str)
            if not df_ukoly.empty:
                try:
                    cz_tz = pytz.timezone('Europe/Prague')
                    dnesni_datum = datetime.now(cz_tz).date()
                except:
                    dnesni_datum = datetime.now().date()
                    
                for idx, row_u in df_ukoly.iterrows():
                    try:
                        t_date = datetime.strptime(row_u["Termín"], "%d.%m.%Y").date()
                        dny_rozdil = (t_date - dnesni_datum).days
                        status_badge = "🔴 DNES HOŘÍ / PROŠLÉ!" if dny_rozdil < 0 else ("⚠️ Blíží se (Akutní)" if dny_rozdil <= 2 else "🟢 V plánu")
                    except:
                        status_badge = "🟢 V plánu"
                        
                    with st.container(border=True):
                        st.markdown(f"**Status: {status_badge}**")
                        st.markdown(f"📅 **Kdy:** {row_u['Termín']} | 🏢 **Klient:** {row_u['Klient']}")
                        st.markdown(f"📝 **Důvod:** {row_u['Důvod (Kvůli čemu)']}")
                        
                        col_c1, col_c2 = st.columns(2)
                        tel_val = str(row_u['Telefon']).strip() if 'Telefon' in row_u and pd.notna(row_u['Telefon']) else ""
                        mail_val = str(row_u['Email']).strip() if 'Email' in row_u and pd.notna(row_u['Email']) else ""
                        
                        with col_c1:
                            if tel_val and tel_val != "nan" and tel_val != "":
                                st.markdown(f'<a href="tel:{tel_val}" style="text-decoration:none;"><button style="width:100%; height:36px; background-color:#2E7D32; color:white; border:none; border-radius:5px; font-weight:bold; font-size:12px; cursor:pointer;">📞 ZAVOLAT: {tel_val}</button></a>', unsafe_allow_html=True)
                        with col_c2:
                            if mail_val and mail_val != "nan" and mail_val != "":
                                st.markdown(f'<a href="mailto:{mail_val}" style="text-decoration:none;"><button style="width:100%; height:36px; background-color:#1565C0; color:white; border:none; border-radius:5px; font-weight:bold; font-size:12px; cursor:pointer;">✉️ NAPÍSAT E-MAIL</button></a>', unsafe_allow_html=True)
                        
                        st.write("")
                        if st.button(f"✅ Vyřízeno (Smazat připomínku)", key=f"del_task_btn_{idx}", use_container_width=True):
                            df_upraveny_ukoly = df_ukoly.drop(df_ukoly.index[idx])
                            df_upraveny_ukoly.to_csv(UKOLY_SOUBOR, index=False, encoding="utf-8")
                            st.success("Úkol úspěšně vyřízen!")
                            st.rerun()
            else: st.caption("Nemáte žádné naplánované připomínky.")
        except: st.caption("Nemáte žádné naplánované připomínky.")
    else: st.caption("Nemáte žádné naplánované připomínky.")

    st.write("---")
    with st.expander("🗑️ Správa databáze a čistění"):
        if os.path.exists(HISTORIE_SOUBOR):
            df_hist = pd.read_csv(HISTORIE_SOUBOR, dtype=str)
            row_lbl = "Zadejte číslo řádku ke smazání z deníku:" if jazyk == "CS" else "Enter row number to delete from log:"
            radek_ke_smaza = st.number_input(row_lbl, min_value=1, max_value=len(df_hist), step=1)
            if st.button("❌ Smazat tento řádek z deníku", use_container_width=True):
                df_upraveny = df_hist.drop(df_hist.index[radek_ke_smaza - 1])
                df_upraveny.to_csv(HISTORIE_SOUBOR, index=False, encoding="utf-8")
                st.success("Smazáno!")
                st.rerun()
            
        if st.button("🚨 VYČISTIT ÚPLNĚ VŠE (Deník i Připomínky)", use_container_width=True):
            if os.path.exists(HISTORIE_SOUBOR): os.remove(HISTORIE_SOUBOR)
            if os.path.exists(EXPORT_FILE): os.remove(EXPORT_FILE)
            if os.path.exists(UKOLY_SOUBOR): os.remove(UKOLY_SOUBOR)
            st.success("Vše kompletně vyčištěno!")
            st.rerun()
    
    if os.path.exists(HISTORIE_SOUBOR):
        df_hist = pd.read_csv(HISTORIE_SOUBOR, dtype=str)
        xl_btn_lbl = "📥 Stáhnout deník jako záložní CSV soubor (.csv)" if jazyk == "CS" else "📥 Download log as backup CSV file (.csv)"
        csv_buffer = df_hist.copy()
        if "RawText_Zaloha" in csv_buffer.columns: csv_buffer = csv_buffer.drop(columns=["RawText_Zaloha"])
        csv_data_data = csv_buffer.to_csv(index=False, encoding="utf-8")
        st.download_button(label=xl_btn_lbl, data=csv_data_data, file_name=f"routereport_export.csv", mime="text/csv", use_container_width=True)
if __name__ == "__main__":
    TAJNE_HESLO = "Cestak123"
    
    # Držíme stav přihlášení přímo v bezpečné paměti serveru Streamlitu.
    # Prohlížeč už nemá šanci program sám od sebe uspat nebo odhlásit!
    if "prihlasen_trvale" not in st.session_state:
        st.session_state["prihlasen_trvale"] = False

    if not st.session_state["prihlasen_trvale"]:
        st.subheader("🔒 RouteReport - Private Access")
        vstoupit_heslo = st.text_input("Zadejte přístupové heslo / Enter Password:", type="password")
        if st.button("Vstoupit do aplikace / Enter App", use_container_width=True):
            if vstoupit_heslo == TAJNE_HESLO:
                st.session_state["prihlasen_trvale"] = True
                st.rerun()
            else:
                st.error("❌ Nesprávné heslo! Přístup odepřen / Access Denied.")
    else:
        vykresli_aplikaci()
