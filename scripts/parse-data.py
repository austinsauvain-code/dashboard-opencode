#!/usr/bin/env python3
"""
parse-data.py — Analyse universelle de fichiers de données (CSV, Excel, ZIP).

Détecte automatiquement le domaine (ventes, RH, ads, SEO, analytics, support, CRM)
et produit un JSON structuré avec KPIs, classement des colonnes, et anomalies.

Usage:
    python3 scripts/parse-data.py input/fichier.csv [--output output/analyse.json]
    python3 scripts/parse-data.py input/fichier.xlsx [--sheet "Feuil1"]
    python3 scripts/parse-data.py input/archive.zip [--mois mars]
"""

import csv, json, os, sys, argparse, zipfile, tempfile, shutil, re
from datetime import datetime
from pathlib import Path
from collections import Counter

# Optionnel : pandas pour Excel
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False


# ══════════════════════════════════════════════
# DÉTECTION DE DOMAINE
# ══════════════════════════════════════════════

DOMAIN_SIGNALS = {
    'ads': ['cpc', 'ctr', 'impressions', 'conversions', 'mots-clés', 'groupes d\'annonces',
            'campagne', 'budget', 'enchère', 'roas', 'cpa', 'ad group', 'clicks', 'cost'],
    'ecommerce': ['ca', 'chiffre', 'quantité', 'panier', 'produit', 'catégorie', 'montant',
                  'prix', 'commande', 'client', 'vente', 'revenue', 'order'],
    'rh': ['salaire', 'ancienneté', 'département', 'évaluation', 'embauche', 'poste',
           'employé', 'salarié', 'turnover', 'effectif', 'salary', 'department'],
    'analytics': ['trafic', 'pages vues', 'rebond', 'sessions', 'sources', 'visiteurs',
                  'pageviews', 'bounce', 'session', 'users', 'organic'],
    'support': ['tickets', 'résolution', 'satisfaction', 'agent', 'statut', 'priorité',
                'sla', 'csat', 'escalade', 'ticket', 'resolution'],
    'crm': ['leads', 'pipeline', 'étape', 'probabilité', 'commercial', 'deal',
            'opportunity', 'stage', 'win rate', 'prospect'],
    'seo': ['position', 'requêtes', 'pages les plus', 'search console', 'clics',
            'impressions', 'ctr', 'hreflang'],
}

def detect_domain(columns, sample_values=None):
    """Détecte le domaine des données à partir des noms de colonnes."""
    cols_lower = ' '.join(c.lower() for c in columns)
    if sample_values:
        cols_lower += ' ' + ' '.join(str(v).lower() for v in sample_values[:50])
    
    scores = {}
    for domain, signals in DOMAIN_SIGNALS.items():
        score = sum(1 for s in signals if s in cols_lower)
        if score > 0:
            scores[domain] = score
    
    if scores:
        return max(scores, key=scores.get)
    return 'general'


# ══════════════════════════════════════════════
# CLASSIFICATION DES COLONNES
# ══════════════════════════════════════════════

def classify_column(name, values):
    """Classe une colonne : numeric, categorical, date, text."""
    name_lower = name.lower()
    non_empty = [v for v in values if v and str(v).strip()]
    
    if not non_empty:
        return 'empty'
    
    # Essayer date
    date_signals = ['date', 'jour', 'mois', 'année', 'period', 'time', 'created', 'updated']
    if any(s in name_lower for s in date_signals):
        return 'date'
    
    # Essayer numérique
    numeric_count = 0
    for v in non_empty[:100]:
        try:
            cleaned = str(v).replace('%', '').replace('€', '').replace('$', '').replace(',', '.').replace(' ', '').strip()
            if cleaned:
                float(cleaned)
                numeric_count += 1
        except (ValueError, TypeError):
            pass
    
    if numeric_count / max(len(non_empty[:100]), 1) > 0.7:
        return 'numeric'
    
    # Catégoriel vs texte
    distinct = len(set(str(v) for v in non_empty))
    total = len(non_empty)
    
    if distinct <= 50 or distinct / total < 0.3:
        return 'categorical'
    
    return 'text'


def parse_numeric(val):
    """Parse une valeur numérique, gère %, €, espaces."""
    if val is None or str(val).strip() == '':
        return None
    s = str(val).replace('%', '').replace('€', '').replace('$', '').replace(',', '.').replace('\xa0', '').replace(' ', '').strip()
    try:
        return float(s)
    except (ValueError, TypeError):
        return None


# ══════════════════════════════════════════════
# LECTEURS DE FICHIERS
# ══════════════════════════════════════════════

def read_csv_file(filepath):
    """Lit un CSV et retourne (colonnes, lignes)."""
    rows = []
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        # Détecter le séparateur
        sample = f.read(4096)
        f.seek(0)
        
        if sample.count('\t') > sample.count(',') and sample.count('\t') > sample.count(';'):
            sep = '\t'
        elif sample.count(';') > sample.count(','):
            sep = ';'
        else:
            sep = ','
        
        reader = csv.DictReader(f, delimiter=sep)
        columns = reader.fieldnames or []
        for row in reader:
            rows.append(row)
    
    return columns, rows


def read_excel_file(filepath, sheet=None):
    """Lit un fichier Excel et retourne (colonnes, lignes, sheets)."""
    if not HAS_PANDAS:
        print("❌ pandas requis pour les fichiers Excel. Installer : pip3 install pandas openpyxl", file=sys.stderr)
        sys.exit(1)
    
    xls = pd.ExcelFile(filepath)
    sheet_names = xls.sheet_names
    target_sheet = sheet or sheet_names[0]
    
    df = pd.read_excel(filepath, sheet_name=target_sheet)
    columns = list(df.columns.astype(str))
    rows = df.to_dict('records')
    
    return columns, rows, sheet_names


def read_input(filepath, sheet=None):
    """Lit n'importe quel fichier supporté et retourne un dict structuré."""
    ext = Path(filepath).suffix.lower()
    all_files = {}
    
    if ext == '.zip':
        tmpdir = tempfile.mkdtemp()
        with zipfile.ZipFile(filepath, 'r') as z:
            z.extractall(tmpdir)
        
        for f in sorted(os.listdir(tmpdir)):
            fpath = os.path.join(tmpdir, f)
            if f.lower().endswith('.csv'):
                cols, rows = read_csv_file(fpath)
                all_files[f] = {'columns': cols, 'rows': rows}
            elif f.lower().endswith(('.xlsx', '.xls')):
                cols, rows, sheets = read_excel_file(fpath, sheet)
                all_files[f] = {'columns': cols, 'rows': rows, 'sheets': sheets}
        
        shutil.rmtree(tmpdir, ignore_errors=True)
    
    elif ext == '.csv':
        cols, rows = read_csv_file(filepath)
        all_files[os.path.basename(filepath)] = {'columns': cols, 'rows': rows}
    
    elif ext in ('.xlsx', '.xls'):
        cols, rows, sheets = read_excel_file(filepath, sheet)
        all_files[os.path.basename(filepath)] = {'columns': cols, 'rows': rows, 'sheets': sheets}
    
    else:
        print(f"❌ Format non supporté : {ext}", file=sys.stderr)
        sys.exit(1)
    
    return all_files


# ══════════════════════════════════════════════
# ANALYSE PRINCIPALE
# ══════════════════════════════════════════════

def analyze(all_files, mois_filtre=None):
    """Analyse complète de tous les fichiers."""
    
    result = {
        'source': list(all_files.keys()),
        'parsed_at': datetime.now().isoformat(),
        'files': {},
        'domain': 'general',
        'summary': {},
    }
    
    all_columns = []
    
    for fname, fdata in all_files.items():
        cols = fdata['columns']
        rows = fdata['rows']
        all_columns.extend(cols)
        
        # Classifier chaque colonne
        col_classes = {}
        for col in cols:
            values = [row.get(col, '') for row in rows]
            col_classes[col] = classify_column(col, values)
        
        # Identifier les métriques numériques
        metrics = {col: cls for col, cls in col_classes.items() if cls == 'numeric'}
        dimensions = {col: cls for col, cls in col_classes.items() if cls == 'categorical'}
        dates = {col: cls for col, cls in col_classes.items() if cls == 'date'}
        texts = {col: cls for col, cls in col_classes.items() if cls == 'text'}
        empties = {col: cls for col, cls in col_classes.items() if cls == 'empty'}
        
        # Calculer les KPIs pour chaque métrique
        kpis = {}
        for col in metrics:
            vals = [parse_numeric(row.get(col)) for row in rows]
            vals = [v for v in vals if v is not None]
            if vals:
                kpis[col] = {
                    'total': round(sum(vals), 2),
                    'moyenne': round(sum(vals) / len(vals), 2),
                    'min': round(min(vals), 2),
                    'max': round(max(vals), 2),
                    'count': len(vals),
                    'missing': len(rows) - len(vals),
                }
        
        # Calculer les répartitions pour chaque dimension
        distributions = {}
        for col in dimensions:
            counter = Counter(str(row.get(col, '')).strip() for row in rows if row.get(col))
            top = counter.most_common(20)
            distributions[col] = {
                'distinct': len(counter),
                'top': [{'value': v, 'count': c} for v, c in top],
            }
        
        # Timeline si date trouvée
        timeline = None
        if dates:
            date_col = list(dates.keys())[0]
            timeline = []
            for row in rows:
                entry = {'date': str(row.get(date_col, ''))}
                for mcol in metrics:
                    entry[mcol] = parse_numeric(row.get(mcol))
                timeline.append(entry)
        
        # Filtrer par mois si demandé
        if mois_filtre and timeline:
            mois_map = {
                'janvier':'01','février':'02','mars':'03','avril':'04','mai':'05',
                'juin':'06','juillet':'07','août':'08','septembre':'09',
                'octobre':'10','novembre':'11','décembre':'12',
            }
            mnum = mois_map.get(mois_filtre.lower(), mois_filtre.zfill(2))
            timeline = [e for e in timeline if f"-{mnum}-" in str(e.get('date','')) or str(e.get('date','')).startswith(f"2026-{mnum}") or str(e.get('date','')).startswith(f"2025-{mnum}")]
        
        result['files'][fname] = {
            'rows': len(rows),
            'columns': cols,
            'classification': col_classes,
            'metrics': list(metrics.keys()),
            'dimensions': list(dimensions.keys()),
            'dates': list(dates.keys()),
            'texts': list(texts.keys()),
            'empties': list(empties.keys()),
            'kpis': kpis,
            'distributions': distributions,
            'timeline': timeline,
            'sample_rows': rows[:5],
        }
    
    # Détecter le domaine
    result['domain'] = detect_domain(all_columns)
    
    # Résumé global
    total_rows = sum(f['rows'] for f in result['files'].values())
    all_metrics = []
    all_dims = []
    for f in result['files'].values():
        all_metrics.extend(f['metrics'])
        all_dims.extend(f['dimensions'])
    
    result['summary'] = {
        'total_files': len(all_files),
        'total_rows': total_rows,
        'total_columns': len(set(all_columns)),
        'domain': result['domain'],
        'metrics': list(set(all_metrics)),
        'dimensions': list(set(all_dims)),
    }
    
    return result


# ══════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description='Analyse universelle de fichiers de données')
    parser.add_argument('input', help='Fichier à analyser (.csv, .xlsx, .zip)')
    parser.add_argument('--output', '-o', help='Fichier JSON de sortie')
    parser.add_argument('--sheet', '-s', help='Feuille Excel à lire')
    parser.add_argument('--mois', '-m', help='Filtrer sur un mois (ex: mars)')
    parser.add_argument('--pretty', action='store_true', help='JSON formaté')
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"❌ Fichier introuvable : {args.input}", file=sys.stderr)
        sys.exit(1)
    
    print(f"📦 Lecture de {args.input}...")
    all_files = read_input(args.input, args.sheet)
    
    print(f"🔍 Analyse de {len(all_files)} fichier(s)...")
    result = analyze(all_files, args.mois)
    
    # Afficher le résumé
    s = result['summary']
    print(f"\n{'='*50}")
    print(f"📊 Analyse du fichier :")
    print(f"   Fichiers : {s['total_files']} | Lignes : {s['total_rows']} | Colonnes : {s['total_columns']}")
    print(f"   Domaine détecté : {s['domain'].upper()}")
    print(f"   Métriques : {', '.join(s['metrics']) or 'aucune'}")
    print(f"   Dimensions : {', '.join(s['dimensions']) or 'aucune'}")
    
    for fname, fdata in result['files'].items():
        if fdata.get('empties'):
            print(f"   ⚠️  Colonnes vides dans {fname} : {', '.join(fdata['empties'])}")
    print(f"{'='*50}\n")
    
    # Sauvegarder
    indent = 2 if args.pretty else None
    json_str = json.dumps(result, ensure_ascii=False, indent=indent, default=str)
    
    if args.output:
        os.makedirs(os.path.dirname(args.output) or '.', exist_ok=True)
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(json_str)
        print(f"✅ Analyse exportée → {args.output}")
    else:
        print(json_str)


if __name__ == '__main__':
    main()
