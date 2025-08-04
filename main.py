import streamlit as st
import pandas as pd
import json
from datetime import datetime, date
import os
from typing import Dict, List, Any
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
import io
import re

# Configuration de la page
try:
    st.set_page_config(
        page_title="Budget Garderie",
        page_icon="👶",
        layout="wide"
    )
except Exception:
    pass

class GarderieBudget:
    def __init__(self, user_id: str):
        self.user_id = re.sub(r'\W+', '_', user_id.lower())[:30]
        self.data_file = f"garderie_budget_{self.user_id}.json"

        self.months = [
            'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
            'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
        ]

        self.revenue_categories = [
            'Frais de garde',
            'Subventions gouvernementales',
            "Frais d'inscription",
            'Activités spéciales',
            'Autres revenus'
        ]

        self.expense_categories = [
            'Salaires et avantages',
            'Alimentation',
            'Matériel éducatif',
            'Fournitures',
            'Loyer/Hypothèque',
            'Services publics',
            'Assurances',
            'Entretien et réparations',
            'Formation du personnel',
            'Autres dépenses'
        ]

        self.session_key = f'budget_data_{self.user_id}'
        if self.session_key not in st.session_state:
            st.session_state[self.session_key] = self.load_data()

    def load_data(self) -> Dict:
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            st.error(f"Erreur lors du chargement des données: {e}")
            return {}

    def save_data(self):
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(st.session_state[self.session_key], f, ensure_ascii=False, indent=2)
            st.success("Données sauvegardées avec succès!")
        except Exception as e:
            st.error(f"Erreur lors de la sauvegarde: {e}")

    def get_month_key(self, year: int, month: int) -> str:
        return f"{year}-{month}"

    def get_month_data(self, year: int, month: int) -> Dict:
        key = self.get_month_key(year, month)
        if key not in st.session_state[self.session_key]:
            st.session_state[self.session_key][key] = {
                'revenues': [],
                'expenses': [],
                'notes': ''
            }
        return st.session_state[self.session_key][key]

    def add_revenue(self, year: int, month: int, category: str, description: str, amount: float, date_entry: date):
        month_data = self.get_month_data(year, month)
        revenue = {
            'id': len(month_data['revenues']) + 1,
            'category': category,
            'description': description,
            'amount': amount,
            'date': date_entry.isoformat()
        }
        month_data['revenues'].append(revenue)
        st.session_state[self.session_key][self.get_month_key(year, month)] = month_data

    def add_expense(self, year: int, month: int, category: str, description: str, amount: float, date_entry: date):
        month_data = self.get_month_data(year, month)
        expense = {
            'id': len(month_data['expenses']) + 1,
            'category': category,
            'description': description,
            'amount': amount,
            'date': date_entry.isoformat()
        }
        month_data['expenses'].append(expense)
        st.session_state[self.session_key][self.get_month_key(year, month)] = month_data

    def delete_item(self, year: int, month: int, item_type: str, item_id: int):
        month_data = self.get_month_data(year, month)
        month_data[item_type] = [item for item in month_data[item_type] if item['id'] != item_id]
        st.session_state[self.session_key][self.get_month_key(year, month)] = month_data

    def calculate_totals(self, year: int, month: int) -> Dict[str, float]:
        month_data = self.get_month_data(year, month)
        total_revenues = sum(item['amount'] for item in month_data['revenues'])
        total_expenses = sum(item['amount'] for item in month_data['expenses'])
        return {
            'revenues': total_revenues,
            'expenses': total_expenses,
            'net_income': total_revenues - total_expenses
        }

    def generate_annual_report(self, year: int) -> Dict:
        annual_data = {
            'monthly_totals': [],
            'revenue_categories': {cat: 0 for cat in self.revenue_categories},
            'expense_categories': {cat: 0 for cat in self.expense_categories},
            'grand_totals': {'revenues': 0, 'expenses': 0, 'net_income': 0}
        }
        for month in range(12):
            data = self.get_month_data(year, month)
            totals = self.calculate_totals(year, month)
            annual_data['monthly_totals'].append({
                'month': self.months[month],
                'revenues': totals['revenues'],
                'expenses': totals['expenses'],
                'net_income': totals['net_income']
            })
            for rev in data['revenues']:
                annual_data['revenue_categories'][rev['category']] += rev['amount']
            for exp in data['expenses']:
                annual_data['expense_categories'][exp['category']] += exp['amount']
            annual_data['grand_totals']['revenues'] += totals['revenues']
            annual_data['grand_totals']['expenses'] += totals['expenses']
        annual_data['grand_totals']['net_income'] = (
            annual_data['grand_totals']['revenues'] - annual_data['grand_totals']['expenses']
        )
        return annual_data

    def generate_monthly_pdf(self, year: int, month: int = None) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        story = []
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='CenterTitle', alignment=TA_CENTER, fontSize=16, spaceAfter=12))

        months_to_include = [month] if month is not None else list(range(12))

        for m in months_to_include:
            totals = self.calculate_totals(year, m)
            story.append(Paragraph(f"Rapport mensuel - {self.months[m]} {year}", styles['CenterTitle']))
            story.append(Paragraph(f"Revenus: {totals['revenues']:.2f} $", styles['Normal']))
            story.append(Paragraph(f"Dépenses: {totals['expenses']:.2f} $", styles['Normal']))
            story.append(Paragraph(f"Résultat net: {totals['net_income']:.2f} $", styles['Normal']))
            story.append(Spacer(1, 12))

            month_data = self.get_month_data(year, m)

            if month_data['revenues']:
                story.append(Paragraph("Revenus:", styles['Heading3']))
                rev_table = [["Catégorie", "Description", "Date", "Montant"]] + [
                    [r['category'], r['description'], r['date'], f"{r['amount']:.2f} $"] for r in month_data['revenues']
                ]
                table = Table(rev_table)
                table.setStyle(TableStyle([
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey)
                ]))
                story.append(table)
                story.append(Spacer(1, 12))

            if month_data['expenses']:
                story.append(Paragraph("Dépenses:", styles['Heading3']))
                exp_table = [["Catégorie", "Description", "Date", "Montant"]] + [
                    [e['category'], e['description'], e['date'], f"{e['amount']:.2f} $"] for e in month_data['expenses']
                ]
                table = Table(exp_table)
                table.setStyle(TableStyle([
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey)
                ]))
                story.append(table)

            story.append(Spacer(1, 24))

        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()

def main():
    st.sidebar.markdown("## 👤 Connexion")
    user_id = st.sidebar.text_input("Votre identifiant (unique)", max_chars=30)
    if not user_id:
        st.warning("Veuillez entrer un identifiant pour continuer.")
        st.stop()

    app = GarderieBudget(user_id)

    # Titre principal
    st.title("👶 Budget Garderie")
    st.markdown("**Gestion budgétaire mensuelle pour garderie**")

    # Sidebar pour la navigation
    st.sidebar.header("Navigation")
    current_year = st.sidebar.selectbox("Année", range(2020, 2031), index=5)
    current_month = st.sidebar.selectbox("Mois", range(12), format_func=lambda x: app.months[x])

    # Boutons de sauvegarde et export
    st.sidebar.markdown("---")
    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("💾 Sauvegarder", use_container_width=True):
            app.save_data()
    with col2:
        month_data = app.get_month_data(current_year, current_month)
        has_data = len(month_data['revenues']) > 0 or len(month_data['expenses']) > 0
        if st.button("📄 PDF", use_container_width=True, disabled=not has_data):
            if has_data:
                try:
                    pdf_bytes = app.generate_monthly_pdf(year=current_year)
                    st.download_button(
                        label="📥 Télécharger PDF",
                        data=pdf_bytes,
                        file_name=f"budget_garderie_{app.months[current_month]}_{current_year}.pdf",
                        mime="application/pdf",
                        use_container_width=True
                    )
                except Exception as e:
                    st.error(f"Erreur lors de la génération du PDF: {e}")
                    st.info("Assurez-vous d'avoir installé reportlab: pip install reportlab")
            else:
                st.warning("Aucune donnée pour ce mois")

    # Calculer les totaux
    totals = app.calculate_totals(current_year, current_month)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("💚 Revenus", f"{totals['revenues']:,.2f} $")
    with col2:
        st.metric("❤️ Dépenses", f"{totals['expenses']:,.2f} $")
    with col3:
        st.metric("💙 Résultat Net", f"{totals['net_income']:,.2f} $")

    # Onglets
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Revenus", "📉 Dépenses", "📝 Notes", "📊 Rapport Annuel"])

    with tab1:
        st.header(f"Revenus - {app.months[current_month]} {current_year}")
        with st.expander("➕ Ajouter un revenu"):
            with st.form("add_revenue"):
                col1, col2 = st.columns(2)
                with col1:
                    rev_category = st.selectbox("Catégorie", app.revenue_categories)
                    rev_amount = st.number_input("Montant ($)", min_value=0.0, step=0.01)
                with col2:
                    rev_description = st.text_input("Description")
                    rev_date = st.date_input("Date", value=date.today())
                if st.form_submit_button("Ajouter le revenu"):
                    if rev_amount > 0:
                        app.add_revenue(current_year, current_month, rev_category, rev_description, rev_amount, rev_date)
                        st.success("Revenu ajouté avec succès!")
                        st.rerun()
                    else:
                        st.error("Le montant doit être supérieur à 0")
        month_data = app.get_month_data(current_year, current_month)
        if month_data['revenues']:
            for revenue in month_data['revenues']:
                with st.expander(f"{revenue['category']} - {revenue['amount']:,.2f} $ ({revenue['date']})"):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**Description:** {revenue['description']}")
                        st.write(f"**Catégorie:** {revenue['category']}")
                        st.write(f"**Date:** {revenue['date']}")
                    with col2:
                        if st.button("🗑️ Supprimer", key=f"del_rev_{revenue['id']}"):
                            app.delete_item(current_year, current_month, 'revenues', revenue['id'])
                            st.rerun()
        else:
            st.info("Aucun revenu enregistré pour ce mois.")

    with tab2:
        st.header(f"Dépenses - {app.months[current_month]} {current_year}")
        with st.expander("➕ Ajouter une dépense"):
            with st.form("add_expense"):
                col1, col2 = st.columns(2)
                with col1:
                    exp_category = st.selectbox("Catégorie", app.expense_categories)
                    exp_amount = st.number_input("Montant ($)", min_value=0.0, step=0.01)
                with col2:
                    exp_description = st.text_input("Description")
                    exp_date = st.date_input("Date", value=date.today())
                if st.form_submit_button("Ajouter la dépense"):
                    if exp_amount > 0:
                        app.add_expense(current_year, current_month, exp_category, exp_description, exp_amount, exp_date)
                        st.success("Dépense ajoutée avec succès!")
                        st.rerun()
                    else:
                        st.error("Le montant doit être supérieur à 0")
        if month_data['expenses']:
            for expense in month_data['expenses']:
                with st.expander(f"{expense['category']} - {expense['amount']:,.2f} $ ({expense['date']})"):
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.write(f"**Description:** {expense['description']}")
                        st.write(f"**Catégorie:** {expense['category']}")
                        st.write(f"**Date:** {expense['date']}")
                    with col2:
                        if st.button("🗑️ Supprimer", key=f"del_exp_{expense['id']}"):
                            app.delete_item(current_year, current_month, 'expenses', expense['id'])
                            st.rerun()
        else:
            st.info("Aucune dépense enregistrée pour ce mois.")

    with tab3:
        st.header(f"Notes - {app.months[current_month]} {current_year}")
        current_notes = month_data.get('notes', '')
        notes = st.text_area("Notes et commentaires pour ce mois:", value=current_notes, height=150)
        if st.button("💾 Sauvegarder les notes"):
            month_data['notes'] = notes
            st.session_state[app.session_key][app.get_month_key(current_year, current_month)] = month_data
            st.success("Notes sauvegardées!")

    with tab4:
        st.header(f"📊 Rapport Annuel {current_year}")
        annual_report = app.generate_annual_report(current_year)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Revenus", f"{annual_report['grand_totals']['revenues']:,.2f} $")
        with col2:
            st.metric("Total Dépenses", f"{annual_report['grand_totals']['expenses']:,.2f} $")
        with col3:
            st.metric("Résultat Net", f"{annual_report['grand_totals']['net_income']:,.2f} $")

        st.subheader("Résumé Mensuel")
        monthly_df = pd.DataFrame(annual_report['monthly_totals'])
        if not monthly_df.empty:
            monthly_df['revenues'] = monthly_df['revenues'].apply(lambda x: f"{x:,.2f} $")
            monthly_df['expenses'] = monthly_df['expenses'].apply(lambda x: f"{x:,.2f} $")
            monthly_df['net_income'] = monthly_df['net_income'].apply(lambda x: f"{x:,.2f} $")
            monthly_df.columns = ['Mois', 'Revenus', 'Dépenses', 'Résultat Net']
            st.dataframe(monthly_df, use_container_width=True)

        st.subheader("Revenus par Catégorie")
        revenue_data = {k: v for k, v in annual_report['revenue_categories'].items() if v > 0}
        if revenue_data:
            st.bar_chart(revenue_data)
        else:
            st.info("Aucun revenu enregistré pour cette année.")

        st.subheader("Dépenses par Catégorie")
        expense_data = {k: v for k, v in annual_report['expense_categories'].items() if v > 0}
        if expense_data:
            st.bar_chart(expense_data)
        else:
            st.info("Aucune dépense enregistrée pour cette année.")

        st.subheader("📄 Export PDF Annuel")
        if st.button("📤 Télécharger tout le rapport annuel en PDF"):
            try:
                pdf_all = app.generate_monthly_pdf(current_year)
                st.download_button(
                    label="📥 Télécharger PDF Annuel",
                    data=pdf_all,
                    file_name=f"rapport_annuel_{current_year}.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            except Exception as e:
                st.error(f"Erreur lors de la génération du PDF annuel: {e}")

    app = GarderieBudget(user_id)
    # Le reste de l'application reste inchangé à partir d'ici (UI, tabs, graphiques, boutons, etc.)

if __name__ == "__main__":
    main()
# Le contenu du script a été précédemment mis à jour, mais a été perdu à cause du reset.
# Nous allons le réécrire automatiquement si nécessaire.
