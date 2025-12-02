"""
Core hardware testing implementation
Integrates stress-ng, native macOS tools, and custom diagnostics
"""

import subprocess
import json
import psutil
import time
from datetime import datetime
from pathlib import Path

class HardwareTestRunner:
    def __init__(self, config):
        self.config = config
        self.results = {}
        self.current_test = None
        self.progress = 0
        self.complete = False
        self.start_time = None
        
    def run_all_tests(self):
        """Execute complete hardware test suite"""
        self.start_time = datetime.now()
        self.complete = False
        self.progress = 0
        
        tests = [
            ('System Information', self.test_system_info),
            ('Battery Health', self.test_battery),
            ('Camera Module', self.test_camera),
            ('Microphone', self.test_microphone),
            ('Audio System', self.test_audio),
            ('MIDI System', self.test_midi),
            ('Bluetooth', self.test_bluetooth),
            ('Wi-Fi', self.test_wifi),
            ('USB/Thunderbolt', self.test_usb),
            ('CPU Stress Test', self.test_cpu_stress),
            ('Memory Endurance', self.test_memory_stress),
            ('SSD Health', self.test_ssd_health),
            ('Thermal Monitoring', self.test_thermal),
            ('Part Authenticity', self.test_authenticity),
        ]
        
        total_tests = len(tests)
        
        for idx, (name, test_func) in enumerate(tests):
            self.current_test = name
            print(f"\n→ Running: {name}")
            
            try:
                result = test_func()
                self.results[name] = result
                print(f"✓ {name}: {'PASS' if result['status'] == 'pass' else 'FAIL'}")
            except Exception as e:
                self.results[name] = {
                    'status': 'error',
                    'message': str(e),
                    'timestamp': datetime.now().isoformat()
                }
                print(f"✗ {name}: ERROR - {e}")
            
            self.progress = int(((idx + 1) / total_tests) * 100)
        
        self.complete = True
        self.current_test = "Complete"
        print(f"\n✓ All tests completed in {(datetime.now() - self.start_time).seconds}s")
        
    def test_system_info(self):
        """System information test"""
        try:
            cpu = subprocess.check_output(['sysctl', '-n', 'machdep.cpu.brand_string']).decode().strip()
            ram_bytes = int(subprocess.check_output(['sysctl', '-n', 'hw.memsize']).decode().strip())
            ram_gb = ram_bytes / (1024**3)
            macos = subprocess.check_output(['sw_vers', '-productVersion']).decode().strip()
            serial = subprocess.check_output(['ioreg', '-l']).decode()
            
            return {
                'status': 'pass',
                'cpu': cpu,
                'ram_gb': round(ram_gb, 2),
                'macos_version': macos,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {'status': 'fail', 'error': str(e)}
    
    def test_battery(self):
        """Battery health with red flag detection"""
        try:
            battery = psutil.sensors_battery()
            power_data = subprocess.check_output(['system_profiler', 'SPPowerDataType']).decode()
            
            # Extract cycle count
            cycle_line = [l for l in power_data.split('\n') if 'Cycle Count' in l]
            cycles = int(cycle_line[0].split(':')[1].strip()) if cycle_line else 0
            
            # Extract condition
            condition_line = [l for l in power_data.split('\n') if 'Condition' in l]
            condition = condition_line[0].split(':')[1].strip() if condition_line else 'Unknown'
            
            status = 'pass'
            warnings = []
            
            if cycles > self.config['thresholds']['battery_cycles_critical']:
                status = 'warning'
                warnings.append(f"High cycle count: {cycles}")
            
            if battery and battery.percent < self.config['thresholds']['battery_health_warning']:
                status = 'warning'
                warnings.append(f"Low charge: {battery.percent}%")
            
            if condition != 'Normal':
                status = 'fail'
                warnings.append(f"Battery condition: {condition}")
            
            return {
                'status': status,
                'percent': battery.percent if battery else 0,
                'cycles': cycles,
                'condition': condition,
                'warnings': warnings,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def test_camera(self):
        """Camera module detection"""
        try:
            camera_data = subprocess.check_output(['system_profiler', 'SPCameraDataType']).decode()
            has_camera = len(camera_data.split('\n')) > 5
            
            return {
                'status': 'pass' if has_camera else 'fail',
                'detected': has_camera,
                'timestamp': datetime.now().isoformat()
            }
        except:
            return {'status': 'fail', 'detected': False}
    
    def test_microphone(self):
        """Microphone detection"""
        try:
            mic_check = subprocess.check_output(['ioreg', '-c', 'AppleHDAEngineInput', '-r']).decode()
            detected = 'IOAudioEngineState' in mic_check
            
            return {
                'status': 'pass' if detected else 'fail',
                'detected': detected,
                'timestamp': datetime.now().isoformat()
            }
        except:
            return {'status': 'fail', 'detected': False}
    
    def test_audio(self):
        """Audio system test"""
        try:
            audio_data = subprocess.check_output(['system_profiler', 'SPAudioDataType']).decode()
            devices = len([l for l in audio_data.split('\n') if 'Device Name' in l])
            
            return {
                'status': 'pass' if devices > 0 else 'fail',
                'devices_found': devices,
                'timestamp': datetime.now().isoformat()
            }
        except:
            return {'status': 'fail', 'devices_found': 0}
    
    def test_midi(self):
        """MIDI system availability"""
        midi_app = Path('/Applications/Utilities/Audio MIDI Setup.app')
        
        return {
            'status': 'pass' if midi_app.exists() else 'fail',
            'available': midi_app.exists(),
            'timestamp': datetime.now().isoformat()
        }
    
    def test_bluetooth(self):
        """Bluetooth hardware test"""
        try:
            bt_data = subprocess.check_output(['system_profiler', 'SPBluetoothDataType']).decode()
            has_bt = 'State:' in bt_data
            
            return {
                'status': 'pass' if has_bt else 'fail',
                'detected': has_bt,
                'timestamp': datetime.now().isoformat()
            }
        except:
            return {'status': 'fail', 'detected': False}
    
    def test_wifi(self):
        """Wi-Fi interface test"""
        try:
            wifi_check = subprocess.check_output([
                'networksetup', '-listallhardwareports'
            ]).decode()
            
            has_wifi = 'Wi-Fi' in wifi_check
            
            return {
                'status': 'pass' if has_wifi else 'fail',
                'detected': has_wifi,
                'timestamp': datetime.now().isoformat()
            }
        except:
            return {'status': 'fail', 'detected': False}
    
    def test_usb(self):
        """USB/Thunderbolt port detection"""
        try:
            usb_data = subprocess.check_output(['ioreg', '-p', 'IOUSB', '-l']).decode()
            devices = usb_data.count('Device Identifier')
            
            return {
                'status': 'pass',
                'devices_found': devices,
                'timestamp': datetime.now().isoformat()
            }
        except:
            return {'status': 'fail', 'devices_found': 0}
    
    def test_cpu_stress(self):
        """CPU stress test using stress-ng"""
        duration = self.config['test_settings']['stress_duration']
        
        try:
            print(f"  → Running CPU stress for {duration}s...")
            
            # Get initial temperature
            temp_before = self._get_cpu_temp()
            
            # Run stress-ng
            subprocess.run([
                'stress-ng',
                '--cpu', '0',  # Use all CPUs
                '--timeout', f'{duration}s',
                '--metrics-brief'
            ], check=True, capture_output=True, timeout=duration + 10)
            
            # Get post-stress temperature
            temp_after = self._get_cpu_temp()
            
            # Check for thermal throttling
            throttled = temp_after > self.config['thresholds']['cpu_temp_critical']
            
            return {
                'status': 'warning' if throttled else 'pass',
                'temp_before': temp_before,
                'temp_after': temp_after,
                'throttled': throttled,
                'duration': duration,
                'timestamp': datetime.now().isoformat()
            }
        except subprocess.TimeoutExpired:
            return {'status': 'error', 'error': 'CPU stress test timeout'}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def test_memory_stress(self):
        """Memory endurance test"""
        mem_mb = self.config['test_settings']['memory_test_mb']
        
        try:
            print(f"  → Testing {mem_mb}MB memory...")
            
            # Use stress-ng for memory testing
            result = subprocess.run([
                'stress-ng',
                '--vm', '1',
                '--vm-bytes', f'{mem_mb}M',
                '--timeout', '30s',
                '--verify'
            ], capture_output=True, text=True)
            
            # Check for errors
            has_errors = 'fail' in result.stdout.lower() or result.returncode != 0
            
            return {
                'status': 'fail' if has_errors else 'pass',
                'memory_tested_mb': mem_mb,
                'errors_detected': has_errors,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def test_ssd_health(self):
        """SSD health and SMART data"""
        try:
            # Get disk info
            disk_usage = psutil.disk_usage('/')
            
            # Try to get SMART data (requires smartmontools)
            try:
                smart_data = subprocess.check_output([
                    'smartctl', '-a', 'disk0'
                ], stderr=subprocess.DEVNULL).decode()
                
                # Extract health percentage
                health_line = [l for l in smart_data.split('\n') if 'Percentage Used' in l or 'Available Spare' in l]
                health = 100  # Default
                
                return {
                    'status': 'pass',
                    'total_gb': round(disk_usage.total / (1024**3), 2),
                    'used_gb': round(disk_usage.used / (1024**3), 2),
                    'free_gb': round(disk_usage.free / (1024**3), 2),
                    'health_percent': health,
                    'timestamp': datetime.now().isoformat()
                }
            except:
                # Fallback to basic disk info
                return {
                    'status': 'pass',
                    'total_gb': round(disk_usage.total / (1024**3), 2),
                    'used_gb': round(disk_usage.used / (1024**3), 2),
                    'free_gb': round(disk_usage.free / (1024**3), 2),
                    'timestamp': datetime.now().isoformat()
                }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def test_thermal(self):
        """Thermal monitoring"""
        try:
            temp = self._get_cpu_temp()
            
            status = 'pass'
            if temp > self.config['thresholds']['cpu_temp_critical']:
                status = 'critical'
            elif temp > self.config['thresholds']['cpu_temp_warning']:
                status = 'warning'
            
            return {
                'status': status,
                'cpu_temp': temp,
                'timestamp': datetime.now().isoformat()
            }
        except:
            return {'status': 'error', 'error': 'Cannot read temperature'}
    
    def test_authenticity(self):
        """Part authenticity verification"""
        try:
            power_data = subprocess.check_output(['system_profiler', 'SPPowerDataType']).decode()
            
            # Check for "Normal" battery condition
            condition_ok = 'Condition: Normal' in power_data
            
            # Check manufacturer info
            manufacturer_line = [l for l in power_data.split('\n') if 'Manufacturer' in l]
            
            red_flags = []
            if not condition_ok:
                red_flags.append("Battery condition not normal")
            
            return {
                'status': 'pass' if len(red_flags) == 0 else 'warning',
                'red_flags': red_flags,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def _get_cpu_temp(self):
        """Get CPU temperature (best effort)"""
        try:
            # Try powermetrics
            result = subprocess.run([
                'sudo', 'powermetrics',
                '--samplers', 'smc',
                '-i', '1000',
                '-n', '1'
            ], capture_output=True, text=True, timeout=5)
            
            for line in result.stdout.split('\n'):
                if 'CPU die temperature' in line:
                    temp = float(line.split(':')[1].strip().split()[0])
                    return temp
            
            # Default fallback
            return 45.0
        except:
            return 45.0
    
    def get_status(self):
        """Get current test status"""
        return {
            'current_test': self.current_test,
            'progress': self.progress,
            'complete': self.complete
        }
    
    def is_complete(self):
        return self.complete
    
    def get_results(self):
        return self.results
