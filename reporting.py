"""
Intelligent red flag detection and report generation
"""

from datetime import datetime
from pathlib import Path
import json

class ReportGenerator:
    def __init__(self, config):
        self.config = config
        self.log_dir = Path(config['logging']['directory'])
        self.log_dir.mkdir(exist_ok=True)
    
    def detect_red_flags(self, results):
        """Detect hardware red flags from test results"""
        red_flags = []
        green_flags = []
        
        # Battery red flags
        if 'Battery Health' in results:
            battery = results['Battery Health']
            if battery['status'] in ['fail', 'warning']:
                for warning in battery.get('warnings', []):
                    red_flags.append({
                        'component': 'Battery',
                        'severity': 'high',
                        'message': warning,
                        'recommendation': 'Consider battery replacement'
                    })
            elif battery['status'] == 'pass':
                green_flags.append('Battery health normal')
        
        # CPU thermal red flags
        if 'CPU Stress Test' in results:
            cpu_test = results['CPU Stress Test']
            if cpu_test.get('throttled'):
                red_flags.append({
                    'component': 'CPU/Thermal',
                    'severity': 'high',
                    'message': f"Thermal throttling detected at {cpu_test['temp_after']}°C",
                    'recommendation': 'Check cooling system, thermal paste may need replacement'
                })
            else:
                green_flags.append('CPU thermal performance optimal')
        
        # Memory red flags
        if 'Memory Endurance' in results:
            mem_test = results['Memory Endurance']
            if mem_test.get('errors_detected'):
                red_flags.append({
                    'component': 'Memory',
                    'severity': 'critical',
                    'message': 'Memory errors detected during stress test',
                    'recommendation': 'CRITICAL: Faulty RAM module - replacement required'
                })
            else:
                green_flags.append('Memory integrity verified')
        
        # Component detection red flags
        failed_components = []
        for test_name in ['Camera Module', 'Microphone', 'Audio System', 'Bluetooth', 'Wi-Fi']:
            if test_name in results and results[test_name]['status'] == 'fail':
                failed_components.append(test_name.replace(' Module', '').replace(' System', ''))
        
        if failed_components:
            red_flags.append({
                'component': 'Hardware Detection',
                'severity': 'medium',
                'message': f"Failed to detect: {', '.join(failed_components)}",
                'recommendation': 'Possible counterfeit or damaged components'
            })
        
        # Authenticity red flags
        if 'Part Authenticity' in results:
            auth = results['Part Authenticity']
            if auth.get('red_flags'):
                for flag in auth['red_flags']:
                    red_flags.append({
                        'component': 'Authenticity',
                        'severity': 'high',
                        'message': flag,
                        'recommendation': 'Verify part authenticity with Apple'
                    })
        
        return {
            'red_flags': red_flags,
            'green_flags': green_flags,
            'total_issues': len(red_flags),
            'health_score': self._calculate_health_score(results, red_flags)
        }
    
    def _calculate_health_score(self, results, red_flags):
        """Calculate overall hardware health score (0-100)"""
        total_tests = len(results)
        passed_tests = sum(1 for r in results.values() if r.get('status') == 'pass')
        
        base_score = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        # Deduct for red flags
        critical_flags = sum(1 for f in red_flags if f.get('severity') == 'critical')
        high_flags = sum(1 for f in red_flags if f.get('severity') == 'high')
        medium_flags = sum(1 for f in red_flags if f.get('severity') == 'medium')
        
        penalty = (critical_flags * 20) + (high_flags * 10) + (medium_flags * 5)
        
        final_score = max(0, base_score - penalty)
        
        return round(final_score, 1)
    
    def generate_summary(self, results):
        """Generate test summary"""
        total = len(results)
        passed = sum(1 for r in results.values() if r.get('status') == 'pass')
        failed = sum(1 for r in results.values() if r.get('status') == 'fail')
        warnings = sum(1 for r in results.values() if r.get('status') == 'warning')
        
        return {
            'total_tests': total,
            'passed': passed,
            'failed': failed,
            'warnings': warnings,
            'pass_rate': round((passed / total) * 100, 1) if total > 0 else 0
        }
    
    def export_full_report(self, results):
        """Export comprehensive report to file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = self.log_dir / f'hardware_report_{timestamp}.json'
        
        red_flags_data = self.detect_red_flags(results)
        summary = self.generate_summary(results)
        
        full_report = {
            'timestamp': datetime.now().isoformat(),
            'summary': summary,
            'red_flags': red_flags_data,
            'detailed_results': results
        }
        
        with open(report_file, 'w') as f:
            json.dump(full_report, f, indent=2)
        
        # Also create human-readable text report
        text_report = self._generate_text_report(full_report)
        text_file = self.log_dir / f'hardware_report_{timestamp}.txt'
        
        with open(text_file, 'w') as f:
            f.write(text_report)
        
        return text_file
    
    def _generate_text_report(self, full_report):
        """Generate human-readable text report"""
        lines = []
        lines.append("=" * 70)
        lines.append("macOS HARDWARE TEST SUITE - COMPREHENSIVE REPORT")
        lines.append("=" * 70)
        lines.append(f"\nGenerated: {full_report['timestamp']}\n")
        
        # Summary
        summary = full_report['summary']
        lines.append("\n📊 TEST SUMMARY")
        lines.append("-" * 70)
        lines.append(f"Total Tests: {summary['total_tests']}")
        lines.append(f"Passed: {summary['passed']}")
        lines.append(f"Failed: {summary['failed']}")
        lines.append(f"Warnings: {summary['warnings']}")
        lines.append(f"Pass Rate: {summary['pass_rate']}%")
        
        # Health Score
        health_score = full_report['red_flags']['health_score']
        lines.append(f"\n🏥 OVERALL HEALTH SCORE: {health_score}/100")
        
        # Red Flags
        red_flags = full_report['red_flags']['red_flags']
        if red_flags:
            lines.append("\n\n🚩 RED FLAGS DETECTED")
            lines.append("-" * 70)
            for flag in red_flags:
                lines.append(f"\n⚠️  {flag['component']} [{flag['severity'].upper()}]")
                lines.append(f"    Issue: {flag['message']}")
                lines.append(f"    Action: {flag['recommendation']}")
        
        # Green Flags
        green_flags = full_report['red_flags']['green_flags']
        if green_flags:
            lines.append("\n\n✅ GREEN FLAGS (Healthy Components)")
            lines.append("-" * 70)
            for flag in green_flags:
                lines.append(f"  ✓ {flag}")
        
        # Detailed Results
        lines.append("\n\n📋 DETAILED TEST RESULTS")
        lines.append("-" * 70)
        for test_name, result in full_report['detailed_results'].items():
            status_symbol = {
                'pass': '✓',
                'fail': '✗',
                'warning': '⚠',
                'error': '❌'
            }.get(result.get('status'), '?')
            
            lines.append(f"\n{status_symbol} {test_name}: {result.get('status', 'unknown').upper()}")
            
            # Add relevant details
            for key, value in result.items():
                if key not in ['status', 'timestamp']:
                    lines.append(f"    {key}: {value}")
        
        lines.append("\n" + "=" * 70)
        lines.append("END OF REPORT")
        lines.append("=" * 70)
        
        return '\n'.join(lines)
