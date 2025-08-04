import streamlit as st
import pandas as pd
import json
from datetime import datetime, date
import os
from typing import Dict, List, Any
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
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
    pass  # Ignore si déjà configuré

# Définir les couleurs modernes
LIGHT_BLUE = colors.HexColor('#e6f0ff')
DARK_BLUE = colors.HexColor('#003366')
LIGHT_GREEN = colors.HexColor('#e6fff2')
DARK_GREEN = colors.HexColor('#006633')
LIGHT_RED = colors.HexColor('#fff2e6')
DARK_RED = colors.HexColor('#cc5200')
GREY_TEXT = colors.HexColor('#555555')
LINE_COLOR = colors.HexColor('#cccccc')

class GarderieBudget:
    def __init__(self):
        self.data_file = "garderie_budget.json"
        self.months = [
            'Janvier', 'Février', 'Mars', 'Avril', 'Mai', 'Juin',
            'Juillet', 'Août', 'Septembre', 'Octobre', 'Novembre', 'Décembre'
        ]
        
        self.revenue_categories = [
            'Frais de garde',
            'Subventions gouvernementales',
            'Frais d\'inscription',
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
        
        # Initialiser les données dans la session
        if 'budget_data' not in st.session_state:
            st.session_state.budget_data = self.load_data()
    
    def load_data(self) -> Dict:
        """Charger les données depuis le fichier JSON"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            st.error(f"Erreur lors du chargement des données: {e}")
            return {}
    
    def save_data(self):
        """Sauvegarder les données dans le fichier JSON"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(st.session_state.budget_data, f, ensure_ascii=False, indent=2)
            st.success("Données sauvegardées avec succès!")
        except Exception as e:
            st.error(f"Erreur lors de la sauvegarde: {e}")
    
    def get_month_key(self, year: int, month: int) -> str:
        """Générer la clé pour un mois donné"""
        return f"{year}-{month}"
    
    def get_month_data(self, year: int, month: int) -> Dict:
        """Obtenir les données pour un mois spécifique"""
        key = self.get_month_key(year, month)
        if key not in st.session_state.budget_data:
            st.session_state.budget_data[key] = {
                'revenues': [],
                'expenses': [],
                'notes': ''
            }
        return st.session_state.budget_data[key]
    
    def add_revenue(self, year: int, month: int, category: str, description: str, amount: float, date_entry: date):
        """Ajouter un revenu"""
        month_data = self.get_month_data(year, month)
        revenue = {
            'id': len(month_data['revenues']) + 1,
            'category': category,
            'description': description,
            'amount': amount,
            'date': date_entry.isoformat()
        }
        month_data['revenues'].append(revenue)
        st.session_state.budget_data[self.get_month_key(year, month)] = month_data
    
    def add_expense(self, year: int, month: int, category: str, description: str, amount: float, date_entry: date):
        """Ajouter une dépense"""
        month_data = self.get_month_data(year, month)
        expense = {
            'id': len(month_data['expenses']) + 1,
            'category': category,
            'description': description,
            'amount': amount,
            'date': date_entry.isoformat()
        }
        month_data['expenses'].append(expense)
        st.session_state.budget_data[self.get_month_key(year, month)] = month_data
    
    def delete_item(self, year: int, month: int, item_type: str, item_id: int):
        """Supprimer un élément"""
        month_data = self.get_month_data(year, month)
        month_data[item_type] = [item for item in month_data[item_type] if item['id'] != item_id]
        st.session_state.budget_data[self.get_month_key(year, month)] = month_data
    
    def calculate_totals(self, year: int, month: int) -> Dict[str, float]:
        """Calculer les totaux pour un mois"""
        month_data = self.get_month_data(year, month)
        total_revenues = sum(item['amount'] for item in month_data['revenues'])
        total_expenses = sum(item['amount'] for item in month_data['expenses'])
        return {
            'revenues': total_revenues,
            'expenses': total_expenses,
            'net_income': total_revenues - total_expenses
        }
    
    def generate_annual_report(self, year: int) -> Dict:
        """Générer le rapport annuel"""
        annual_data = {
            'monthly_totals': [],
            'revenue_categories': {cat: 0 for cat in self.revenue_categories},
            'expense_categories': {cat: 0 for cat in self.expense_categories},
            'grand_totals': {'revenues': 0, 'expenses': 0, 'net_income': 0}
        }
        
        for month in range(12):
            month_data = self.get_month_data(year, month)
            totals = self.calculate_totals(year, month)
            
            annual_data['monthly_totals'].append({
                'month': self.months[month],
                'revenues': totals['revenues'],
                'expenses': totals['expenses'],
                'net_income': totals['net_income']
            })
            
            # Ajouter aux totaux annuels
            annual_data['grand_totals']['revenues'] += totals['revenues']
            annual_data['grand_totals']['expenses'] += totals['expenses']
            
            # Ajouter aux totaux par catégorie
            for item in month_data['revenues']:
                annual_data['revenue_categories'][item['category']] += item['amount']
            
            for item in month_data['expenses']:
                annual_data['expense_categories'][item['category']] += item['amount']
        
        annual_data['grand_totals']['net_income'] = (
            annual_data['grand_totals']['revenues'] - annual_data['grand_totals']['expenses']
        )
        return annual_data
    
    def generate_monthly_pdf(self, year: int, month: int) -> bytes:
        """Générer un PDF pour un mois spécifique avec une apparence modernisée"""
        buffer = io.BytesIO()
        
        # Créer le document PDF
        doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.75*inch, bottomMargin=0.75*inch, leftMargin=0.75*inch, rightMargin=0.75*inch)
        story = []
        
        # Styles
        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name='TitleStyle', fontName='Helvetica-Bold', fontSize=24, alignment=TA_CENTER, textColor=DARK_BLUE, spaceAfter=16))
        styles.add(ParagraphStyle(name='SubtitleStyle', fontName='Helvetica-Bold', fontSize=16, alignment=TA_LEFT, textColor=DARK_BLUE, spaceAfter=8, spaceBefore=16))
        styles.add(ParagraphStyle(name='SummaryHeader', fontName='Helvetica-Bold', fontSize=12, textColor=DARK_BLUE, alignment=TA_LEFT))
        styles.add(ParagraphStyle(name='SummaryValue', fontName='Helvetica', fontSize=12, alignment=TA_RIGHT))
        styles.add(ParagraphStyle(name='FooterStyle', fontName='Helvetica-Oblique', fontSize=8, textColor=colors.grey, alignment=TA_CENTER))
        styles.add(ParagraphStyle(name='TableCaption', fontName='Helvetica-Bold', fontSize=12, textColor=GREY_TEXT, spaceAfter=6))
        styles.add(ParagraphStyle(name='NoteStyle', fontName='Helvetica', fontSize=10, textColor=GREY_TEXT, leading=14, spaceAfter=12))

        # En-tête personnalisé pour le titre
        story.append(Paragraph(f"Rapport Budgétaire Mensuel", styles['TitleStyle']))
        story.append(Paragraph(f"<b>Période:</b> {self.months[month]} {year}", styles['SummaryHeader']))
        story.append(Spacer(1, 0.5*inch))
        
        # Obtenir les données du mois
        month_data = self.get_month_data(year, month)
        totals = self.calculate_totals(year, month)
        
        # Section Résumé financier
        story.append(Paragraph("Résumé Financier", styles['SubtitleStyle']))
        
        summary_data = [
            ['Revenus', f"{totals['revenues']:,.2f} $"],
            ['Dépenses', f"{totals['expenses']:,.2f} $"],
            ['Résultat Net', f"{totals['net_income']:,.2f} $"],
        ]

        summary_table_style = [
            ('BOX', (0,0), (-1,-1), 0.5, LINE_COLOR),
            ('BACKGROUND', (0,0), (-1,-1), LIGHT_BLUE),
            ('GRID', (0,0), (-1,-1), 0.5, LINE_COLOR),
            ('ALIGN', (0,0), (0,-1), 'LEFT'),
            ('ALIGN', (1,0), (1,-1), 'RIGHT'),
            ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
            ('FONTNAME', (1,0), (1,-1), 'Helvetica'),
            ('FONTSIZE', (0,0), (-1,-1), 12),
            ('BOTTOMPADDING', (0,0), (-1,-1), 8),
            ('TOPPADDING', (0,0), (-1,-1), 8),
            ('BACKGROUND', (0, -1), (0, -1), LIGHT_BLUE), # Ligne résultat net
            ('BACKGROUND', (1, -1), (1, -1), LIGHT_BLUE), # Couleur pour le résultat
            ('TEXTCOLOR', (1, -1), (1, -1), colors.green if totals['net_income'] >= 0 else colors.red),
            ('FONTNAME', (1,-1), (1,-1), 'Helvetica-Bold'),
        ]

        summary_table = Table(summary_data, colWidths=[2.5*inch, 2.5*inch])
        summary_table.setStyle(TableStyle(summary_table_style))
        story.append(summary_table)
        story.append(Spacer(1, 0.3*inch))

        # Section Revenus
        if month_data['revenues']:
            story.append(Paragraph("Détails des Revenus", styles['SubtitleStyle']))
            revenue_data = [['Catégorie', 'Description', 'Date', 'Montant']]
            for revenue in month_data['revenues']:
                revenue_data.append([
                    revenue['category'],
                    revenue['description'][:40] + '...' if len(revenue['description']) > 40 else revenue['description'],
                    revenue['date'],
                    f"{revenue['amount']:,.2f} $"
                ])
            
            revenue_table = Table(revenue_data, colWidths=[1.5*inch, 2.5*inch, 1*inch, 1*inch])
            revenue_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), DARK_GREEN),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (2, 0), (2, -1), 'CENTER'),
                ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                ('BACKGROUND', (0, 1), (-1, -1), LIGHT_GREEN),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.white),
            ]))
            story.append(revenue_table)
            story.append(Spacer(1, 0.3*inch))
        
        # Section Dépenses
        if month_data['expenses']:
            story.append(Paragraph("Détails des Dépenses", styles['SubtitleStyle']))
            expense_data = [['Catégorie', 'Description', 'Date', 'Montant']]
            for expense in month_data['expenses']:
                expense_data.append([
                    expense['category'],
                    expense['description'][:40] + '...' if len(expense['description']) > 40 else expense['description'],
                    expense['date'],
                    f"{expense['amount']:,.2f} $"
                ])
            
            expense_table = Table(expense_data, colWidths=[1.5*inch, 2.5*inch, 1*inch, 1*inch])
            expense_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), DARK_RED),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (2, 0), (2, -1), 'CENTER'),
                ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                ('BACKGROUND', (0, 1), (-1, -1), LIGHT_RED),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.white),
            ]))
            story.append(expense_table)
            story.append(Spacer(1, 0.3*inch))
        
        # Section Notes
        if month_data.get('notes', '').strip():
            story.append(Paragraph("Notes et Commentaires", styles['SubtitleStyle']))
            # Remplacer les sauts de ligne pour ReportLab
            notes_text = re.sub(r'\n', '<br/>', month_data['notes'])
            story.append(Paragraph(notes_text, styles['NoteStyle']))
            story.append(Spacer(1, 0.2*inch))
        
        # Fonction pour le pied de page
        def add_footer(canvas, doc):
            canvas.saveState()
            canvas.setFont('Helvetica-Oblique', 8)
            canvas.setFillColor(colors.grey)
            footer_text = f"Rapport généré le {datetime.now().strftime('%d/%m/%Y à %H:%M')}"
            canvas.drawCentredString(A4[0]/2, 0.5 * inch, footer_text)
            canvas.restoreState()

        # Construire le PDF
        doc.build(story, onFirstPage=add_footer, onLaterPages=add_footer)
        buffer.seek(0)
        return buffer.getvalue()

def main():
    # Initialiser l'application
    app = GarderieBudget()
    
    # Titre principal
    st.title("👶 Budget Garderie")
    st.markdown("**Gestion budgétaire mensuelle pour garderie**")
    
    # Sidebar pour la navigation
    st.sidebar.header("Navigation")
    current_year = st.sidebar.selectbox("Année", range(2020, 2031), index=5)  # 2025 par défaut
    current_month = st.sidebar.selectbox("Mois", range(12), format_func=lambda x: app.months[x])
    
    # Boutons de sauvegarde et export
    st.sidebar.markdown("---")
    col1, col2 = st.sidebar.columns(2)
    
    with col1:
        if st.button("💾 Sauvegarder", use_container_width=True):
            app.save_data()
    
    with col2:
        # Bouton d'export PDF mensuel
        month_data = app.get_month_data(current_year, current_month)
        has_data = len(month_data['revenues']) > 0 or len(month_data['expenses']) > 0
        
        if st.button("📄 PDF", use_container_width=True, disabled=not has_data):
            if has_data:
                try:
                    pdf_bytes = app.generate_monthly_pdf(current_year, current_month)
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
    
    # Calculer les totaux du mois actuel
    totals = app.calculate_totals(current_year, current_month)
    
    # Affichage des métriques
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            label="💚 Revenus",
            value=f"{totals['revenues']:,.2f} $",
            delta=None
        )
    
    with col2:
        st.metric(
            label="❤️ Dépenses",
            value=f"{totals['expenses']:,.2f} $",
            delta=None
        )
    
    with col3:
        color = "normal" if totals['net_income'] >= 0 else "inverse"
        st.metric(
            label="💙 Résultat Net",
            value=f"{totals['net_income']:,.2f} $",
            delta=None
        )
    
    # Onglets principaux
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Revenus", "📉 Dépenses", "📝 Notes", "📊 Rapport Annuel"])
    
    # Tab 1: Revenus
    with tab1:
        st.header(f"Revenus - {app.months[current_month]} {current_year}")
        
        # Formulaire d'ajout de revenu
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
        
        # Affichage des revenus
        month_data = app.get_month_data(current_year, current_month)
        if month_data['revenues']:
            revenues_df = pd.DataFrame(month_data['revenues'])
            revenues_df['amount'] = revenues_df['amount'].apply(lambda x: f"{x:,.2f} $")
            
            for i, revenue in enumerate(month_data['revenues']):
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
    
    # Tab 2: Dépenses
    with tab2:
        st.header(f"Dépenses - {app.months[current_month]} {current_year}")
        
        # Formulaire d'ajout de dépense
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
        
        # Affichage des dépenses
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
    
    # Tab 3: Notes
    with tab3:
        st.header(f"Notes - {app.months[current_month]} {current_year}")
        
        current_notes = month_data.get('notes', '')
        notes = st.text_area(
            "Notes et commentaires pour ce mois:",
            value=current_notes,
            height=150,
            help="Ajoutez des notes ou commentaires importants pour ce mois"
        )
        
        if st.button("💾 Sauvegarder les notes"):
            month_data['notes'] = notes
            st.session_state.budget_data[app.get_month_key(current_year, current_month)] = month_data
            st.success("Notes sauvegardées!")
    
    # Tab 4: Rapport Annuel
    with tab4:
        st.header(f"📊 Rapport Annuel {current_year}")
        
        annual_report = app.generate_annual_report(current_year)
        
        # Résumé annuel
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Revenus Annuels", f"{annual_report['grand_totals']['revenues']:,.2f} $")
        with col2:
            st.metric("Total Dépenses Annuelles", f"{annual_report['grand_totals']['expenses']:,.2f} $")
        with col3:
            st.metric("Résultat Net Annuel", f"{annual_report['grand_totals']['net_income']:,.2f} $")
        
        # Tableau mensuel
        st.subheader("Résumé Mensuel")
        monthly_df = pd.DataFrame(annual_report['monthly_totals'])
        if not monthly_df.empty:
            monthly_df['revenues'] = monthly_df['revenues'].apply(lambda x: f"{x:,.2f} $")
            monthly_df['expenses'] = monthly_df['expenses'].apply(lambda x: f"{x:,.2f} $")
            monthly_df['net_income'] = monthly_df['net_income'].apply(lambda x: f"{x:,.2f} $")
            monthly_df.columns = ['Mois', 'Revenus', 'Dépenses', 'Résultat Net']
            st.dataframe(monthly_df, use_container_width=True)
        
        # Graphiques
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Revenus par Catégorie")
            revenue_data = {k: v for k, v in annual_report['revenue_categories'].items() if v > 0}
            if revenue_data:
                st.bar_chart(revenue_data)
            else:
                st.info("Aucun revenu enregistré pour cette année.")
        
        with col2:
            st.subheader("Dépenses par Catégorie")
            expense_data = {k: v for k, v in annual_report['expense_categories'].items() if v > 0}
            if expense_data:
                st.bar_chart(expense_data)
            else:
                st.info("Aucune dépense enregistrée pour cette année.")
        
        # Export du rapport
        if st.button("📥 Exporter le rapport (CSV)"):
            # Créer un DataFrame pour l'export
            export_data = []
            for month_idx in range(12):
                month_data = app.get_month_data(current_year, month_idx)
                for revenue in month_data['revenues']:
                    export_data.append({
                        'Mois': app.months[month_idx],
                        'Type': 'Revenu',
                        'Catégorie': revenue['category'],
                        'Description': revenue['description'],
                        'Montant': revenue['amount'],
                        'Date': revenue['date']
                    })
                for expense in month_data['expenses']:
                    export_data.append({
                        'Mois': app.months[month_idx],
                        'Type': 'Dépense',
                        'Catégorie': expense['category'],
                        'Description': expense['description'],
                        'Montant': expense['amount'],
                        'Date': expense['date']
                    })
            
            if export_data:
                export_df = pd.DataFrame(export_data)
                csv = export_df.to_csv(index=False, encoding='utf-8-sig')
                st.download_button(
                    label="📄 Télécharger CSV",
                    data=csv,
                    file_name=f"rapport_garderie_{current_year}.csv",
                    mime="text/csv"
                )
            else:
                st.warning("Aucune donnée à exporter pour cette année.")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--bare":
        # Mode bare pour éviter les avertissements
        main()
    else:
        main()
