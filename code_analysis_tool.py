# code_analysis_tool.py
"""
Tool to analyze current SAFA system implementation before applying fixes
Run this to understand your current structure and avoid overriding changes
"""

import os
import re
from pathlib import Path

class SAFACodeAnalyzer:
    def __init__(self, project_root):
        self.project_root = Path(project_root)
        self.analysis_results = {}
    
    def analyze_models(self):
        """Analyze current model structure"""
        print("🔍 ANALYZING MODELS...")
        
        # Check registration models
        registration_models = self.project_root / "registration" / "models.py"
        membership_models = self.project_root / "membership" / "models.py"
        accounts_models = self.project_root / "accounts" / "models.py"
        
        results = {
            'registration_models': self._analyze_file(registration_models),
            'membership_models': self._analyze_file(membership_models),
            'accounts_models': self._analyze_file(accounts_models),
        }
        
        self.analysis_results['models'] = results
        return results
    
    def analyze_views(self):
        """Analyze current view implementations"""
        print("🔍 ANALYZING VIEWS...")
        
        registration_views = self.project_root / "registration" / "views.py"
        accounts_views = self.project_root / "accounts" / "views.py"
        
        results = {
            'registration_views': self._analyze_file(registration_views),
            'accounts_views': self._analyze_file(accounts_views),
        }
        
        self.analysis_results['views'] = results
        return results
    
    def analyze_forms(self):
        """Analyze current form implementations"""
        print("🔍 ANALYZING FORMS...")
        
        registration_forms = self.project_root / "registration" / "forms.py"
        accounts_forms = self.project_root / "accounts" / "forms.py"
        
        results = {
            'registration_forms': self._analyze_file(registration_forms),
            'accounts_forms': self._analyze_file(accounts_forms),
        }
        
        self.analysis_results['forms'] = results
        return results
    
    def _analyze_file(self, file_path):
        """Analyze a specific file"""
        if not file_path.exists():
            return {"exists": False, "error": f"File not found: {file_path}"}
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            analysis = {
                "exists": True,
                "file_path": str(file_path),
                "line_count": len(content.split('\n')),
                "models": self._extract_models(content),
                "views": self._extract_views(content),
                "forms": self._extract_forms(content),
                "imports": self._extract_imports(content),
                "inheritance_patterns": self._check_inheritance(content),
                "recent_changes": self._check_recent_patterns(content),
            }
            
            return analysis
            
        except Exception as e:
            return {"exists": True, "error": f"Error reading file: {str(e)}"}
    
    def _extract_models(self, content):
        """Extract model classes from content"""
        models = []
        model_pattern = r'class\s+(\w+)\s*\(([^)]+)\)\s*:'
        matches = re.findall(model_pattern, content)
        
        for match in matches:
            model_name, parent_classes = match
            models.append({
                "name": model_name,
                "parents": [p.strip() for p in parent_classes.split(',')],
                "is_member_subclass": any('Member' in p for p in parent_classes.split(',')),
                "fields": self._extract_model_fields(content, model_name)
            })
        
        return models
    
    def _extract_model_fields(self, content, model_name):
        """Extract fields for a specific model"""
        # Find the model class
        pattern = rf'class\s+{model_name}\s*\([^)]+\)\s*:(.*?)(?=class\s+\w+|$)'
        match = re.search(pattern, content, re.DOTALL)
        
        if not match:
            return []
        
        model_content = match.group(1)
        field_pattern = r'(\w+)\s*=\s*models\.\w+'
        fields = re.findall(field_pattern, model_content)
        
        return fields
    
    def _extract_views(self, content):
        """Extract view functions from content"""
        views = []
        view_pattern = r'def\s+(\w+)\s*\([^)]*\)\s*:'
        matches = re.findall(view_pattern, content)
        
        for match in matches:
            if not match.startswith('_'):  # Skip private methods
                views.append(match)
        
        return views
    
    def _extract_forms(self, content):
        """Extract form classes from content"""
        forms = []
        form_pattern = r'class\s+(\w+Form)\s*\([^)]+\)\s*:'
        matches = re.findall(form_pattern, content)
        
        for match in matches:
            forms.append(match)
        
        return forms
    
    def _extract_imports(self, content):
        """Extract import statements"""
        imports = []
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            if line.startswith('from ') or line.startswith('import '):
                imports.append(line)
        
        return imports
    
    def _check_inheritance(self, content):
        """Check for inheritance patterns"""
        patterns = {
            'multi_table_inheritance': 'Member' in content and 'models.Model' in content,
            'abstract_inheritance': 'abstract = True' in content,
            'proxy_inheritance': 'proxy = True' in content,
            'member_ptr_usage': 'member_ptr' in content,
            'onetoone_usage': 'OneToOneField' in content,
        }
        
        return patterns
    
    def _check_recent_patterns(self, content):
        """Check for recent code patterns that might indicate changes"""
        patterns = {
            'transaction_atomic': '@transaction.atomic' in content,
            'logger_usage': 'logger' in content and 'logging' in content,
            'form_save_commit_false': 'save(commit=False)' in content,
            'member_to_player_conversion': 'member_ptr' in content and 'Player' in content,
            'invoice_creation': 'Invoice.objects.create' in content,
            'club_registration': 'PlayerClubRegistration' in content,
            'utility_functions': 'def create_' in content or 'def convert_' in content,
        }
        
        return patterns
    
    def generate_report(self):
        """Generate comprehensive analysis report"""
        print("\n" + "="*80)
        print("🏆 SAFA SYSTEM CODE ANALYSIS REPORT")
        print("="*80)
        
        # Model Analysis
        if 'models' in self.analysis_results:
            print("\n📊 MODEL ANALYSIS:")
            for file_name, data in self.analysis_results['models'].items():
                if data.get('exists'):
                    print(f"\n  📁 {file_name.upper()}:")
                    print(f"     Lines of code: {data.get('line_count', 0)}")
                    
                    models = data.get('models', [])
                    if models:
                        print("     Models found:")
                        for model in models:
                            inheritance_info = f" (inherits from: {', '.join(model['parents'])})" if model['parents'] != ['models.Model'] else ""
                            member_subclass = " ⚠️  MEMBER SUBCLASS" if model['is_member_subclass'] else ""
                            print(f"       - {model['name']}{inheritance_info}{member_subclass}")
                            if model['fields']:
                                print(f"         Fields: {', '.join(model['fields'])}")
                    
                    # Check inheritance patterns
                    inheritance = data.get('inheritance_patterns', {})
                    if any(inheritance.values()):
                        print("     Inheritance patterns:")
                        for pattern, found in inheritance.items():
                            if found:
                                print(f"       ✅ {pattern}")
                    
                    # Check recent changes
                    recent = data.get('recent_patterns', {})
                    if any(recent.values()):
                        print("     Recent code patterns detected:")
                        for pattern, found in recent.items():
                            if found:
                                print(f"       ✅ {pattern}")
                else:
                    print(f"  ❌ {file_name}: {data.get('error', 'Not found')}")
        
        # View Analysis
        if 'views' in self.analysis_results:
            print("\n🎭 VIEW ANALYSIS:")
            for file_name, data in self.analysis_results['views'].items():
                if data.get('exists'):
                    print(f"\n  📁 {file_name.upper()}:")
                    views = data.get('views', [])
                    if views:
                        print(f"     Views found: {', '.join(views)}")
                    
                    recent = data.get('recent_patterns', {})
                    critical_patterns = ['transaction_atomic', 'member_to_player_conversion', 'invoice_creation']
                    critical_found = [p for p in critical_patterns if recent.get(p)]
                    if critical_found:
                        print(f"     🔥 CRITICAL PATTERNS: {', '.join(critical_found)}")
        
        # Form Analysis
        if 'forms' in self.analysis_results:
            print("\n📝 FORM ANALYSIS:")
            for file_name, data in self.analysis_results['forms'].items():
                if data.get('exists'):
                    print(f"\n  📁 {file_name.upper()}:")
                    forms = data.get('forms', [])
                    if forms:
                        print(f"     Forms found: {', '.join(forms)}")
    
    def check_inheritance_issues(self):
        """Specific check for inheritance issues"""
        print("\n" + "="*80)
        print("⚠️  INHERITANCE ISSUE ANALYSIS")
        print("="*80)
        
        issues = []
        
        # Check if Member subclasses exist
        all_models = []
        for file_data in self.analysis_results.get('models', {}).values():
            if file_data.get('models'):
                all_models.extend(file_data['models'])
        
        member_subclasses = [m for m in all_models if m['is_member_subclass']]
        
        if member_subclasses:
            print(f"\n🎯 FOUND {len(member_subclasses)} MEMBER SUBCLASSES:")
            for model in member_subclasses:
                print(f"   - {model['name']} (parents: {', '.join(model['parents'])})")
                
                # Check if it's using proper inheritance
                if 'member_ptr' not in str(model.get('fields', [])):
                    issues.append(f"{model['name']} may not be using proper multi-table inheritance")
        
        # Check for registration views that might have inheritance issues
        registration_views = self.analysis_results.get('views', {}).get('registration_views', {})
        if registration_views.get('exists'):
            recent_patterns = registration_views.get('recent_patterns', {})
            if not recent_patterns.get('member_to_player_conversion'):
                issues.append("Registration views may not handle Member->Player conversion properly")
        
        if issues:
            print(f"\n🚨 POTENTIAL ISSUES DETECTED:")
            for i, issue in enumerate(issues, 1):
                print(f"   {i}. {issue}")
        else:
            print("\n✅ No obvious inheritance issues detected")
        
        return issues
    
    def recommend_actions(self):
        """Recommend actions based on analysis"""
        print("\n" + "="*80)
        print("💡 RECOMMENDED ACTIONS")
        print("="*80)
        
        # Check what exists and what needs to be updated
        actions = []
        
        # Model recommendations
        models_data = self.analysis_results.get('models', {})
        
        registration_models = models_data.get('registration_models', {})
        if registration_models.get('exists'):
            recent_patterns = registration_models.get('recent_patterns', {})
            if not recent_patterns.get('member_to_player_conversion'):
                actions.append({
                    'priority': 'HIGH',
                    'action': 'Update registration/models.py',
                    'reason': 'Add proper multi-table inheritance and utility functions',
                    'safe': True
                })
        
        # View recommendations
        views_data = self.analysis_results.get('views', {})
        registration_views = views_data.get('registration_views', {})
        if registration_views.get('exists'):
            recent_patterns = registration_views.get('recent_patterns', {})
            if not recent_patterns.get('transaction_atomic'):
                actions.append({
                    'priority': 'HIGH',
                    'action': 'Update registration/views.py',
                    'reason': 'Fix registration logic to create proper Player/Official instances',
                    'safe': False,  # Might override existing changes
                })
        
        # Management command recommendation
        actions.append({
            'priority': 'MEDIUM',
            'action': 'Create management command',
            'reason': 'Fix existing data that has inheritance issues',
            'safe': True
        })
        
        print("\n📋 ACTION PLAN:")
        for i, action in enumerate(actions, 1):
            priority_color = "🔴" if action['priority'] == 'HIGH' else "🟡" if action['priority'] == 'MEDIUM' else "🟢"
            safe_indicator = "✅ SAFE" if action['safe'] else "⚠️  REVIEW NEEDED"
            print(f"\n{i}. {priority_color} {action['priority']} - {action['action']}")
            print(f"   Reason: {action['reason']}")
            print(f"   Safety: {safe_indicator}")
        
        return actions


def main():
    """Run the analysis"""
    print("🚀 SAFA System Code Analyzer")
    print("This tool will analyze your current code to avoid overriding changes")
    
    # Get project root (adjust this path to your actual project root)
    project_root = input("\nEnter your project root path (or press Enter for current directory): ").strip()
    if not project_root:
        project_root = "."
    
    analyzer = SAFACodeAnalyzer(project_root)
    
    # Run analysis
    analyzer.analyze_models()
    analyzer.analyze_views()
    analyzer.analyze_forms()
    
    # Generate reports
    analyzer.generate_report()
    analyzer.check_inheritance_issues()
    analyzer.recommend_actions()
    
    print("\n" + "="*80)
    print("✅ ANALYSIS COMPLETE")
    print("="*80)
    print("\nNext steps:")
    print("1. Review the analysis above")
    print("2. Backup your current code")
    print("3. Apply recommended changes carefully")
    print("4. Test thoroughly before deploying")


if __name__ == "__main__":
    main()
