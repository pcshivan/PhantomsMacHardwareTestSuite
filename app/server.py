"""
Flask web server for hardware testing interface
"""

from flask import Flask, render_template, jsonify, request
import yaml
import threading
import time
from pathlib import Path

from .hardware_tests import HardwareTestRunner
from .reporting import ReportGenerator

app = Flask(__name__)

# Load configuration
config_path = Path(__file__).parent.parent / 'config.yaml'
with open(config_path) as f:
    config = yaml.safe_load(f)

# Global test runner
test_runner = None
report_gen = ReportGenerator(config)

@app.route('/')
def index():
    """Main testing interface"""
    return render_template('index.html')

@app.route('/api/start_tests', methods=['POST'])
def start_tests():
    """Start automated hardware tests"""
    global test_runner
    
    test_types = request.json.get('tests', 'all')
    
    test_runner = HardwareTestRunner(config)
    
    # Run tests in background thread
    thread = threading.Thread(target=test_runner.run_all_tests)
    thread.daemon = True
    thread.start()
    
    return jsonify({'status': 'started', 'message': 'Tests initiated successfully'})

@app.route('/api/test_status')
def test_status():
    """Get current test status"""
    if test_runner:
        status = test_runner.get_status()
        return jsonify(status)
    return jsonify({'status': 'idle', 'progress': 0})

@app.route('/api/results')
def get_results():
    """Get test results with red flag detection"""
    if test_runner and test_runner.is_complete():
        results = test_runner.get_results()
        red_flags = report_gen.detect_red_flags(results)
        
        return jsonify({
            'results': results,
            'red_flags': red_flags,
            'summary': report_gen.generate_summary(results)
        })
    return jsonify({'status': 'not_ready'})

@app.route('/api/export_report')
def export_report():
    """Export full test report"""
    if test_runner:
        report_path = report_gen.export_full_report(test_runner.get_results())
        return jsonify({'report_path': str(report_path)})
    return jsonify({'error': 'No test data available'})

def start_server():
    """Start Flask server"""
    host = config['web_server']['host']
    port = config['web_server']['port']
    debug = config['web_server']['debug']
    
    print(f"\n✓ Server starting at http://{host}:{port}")
    print(f"✓ Open your browser to begin testing\n")
    
    app.run(host=host, port=port, debug=debug)
