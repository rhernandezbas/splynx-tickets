from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
import os
import re
from collections import defaultdict

logs_bp = Blueprint('logs', __name__, url_prefix='/api/logs')

LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs', 'app_splynx.log')

def parse_log_line(line):
    """Parse a log line into structured data"""
    pattern = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) - ([\w\.]+) - (\w+) - (.+)'
    match = re.match(pattern, line.strip())
    
    if match:
        timestamp_str, logger_name, level, message = match.groups()
        return {
            'timestamp': timestamp_str,
            'logger': logger_name,
            'level': level,
            'message': message
        }
    return None

@logs_bp.route('/', methods=['GET'])
def get_logs():
    """Get logs with filters"""
    try:
        level_filter = request.args.get('level', 'all')
        search_query = request.args.get('search', '').lower()
        hours = int(request.args.get('hours', 24))
        limit = int(request.args.get('limit', 500))
        
        if not os.path.exists(LOG_FILE):
            return jsonify({
                'success': True,
                'logs': [],
                'total': 0,
                'message': 'Log file not found'
            }), 200
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        logs = []
        
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            
        for line in reversed(lines[-10000:]):
            parsed = parse_log_line(line)
            if not parsed:
                continue
            
            try:
                log_time = datetime.strptime(parsed['timestamp'], '%Y-%m-%d %H:%M:%S')
                if log_time < cutoff_time:
                    continue
            except:
                continue
            
            if level_filter != 'all' and parsed['level'] != level_filter:
                continue
            
            if search_query and search_query not in parsed['message'].lower():
                continue
            
            logs.append(parsed)
            
            if len(logs) >= limit:
                break
        
        return jsonify({
            'success': True,
            'logs': logs,
            'total': len(logs)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@logs_bp.route('/stats', methods=['GET'])
def get_log_stats():
    """Get log statistics"""
    try:
        hours = int(request.args.get('hours', 24))
        
        if not os.path.exists(LOG_FILE):
            return jsonify({
                'success': True,
                'stats': {
                    'total': 0,
                    'by_level': {},
                    'by_logger': {}
                }
            }), 200
        
        cutoff_time = datetime.now() - timedelta(hours=hours)
        level_counts = defaultdict(int)
        logger_counts = defaultdict(int)
        total = 0
        
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        for line in reversed(lines[-10000:]):
            parsed = parse_log_line(line)
            if not parsed:
                continue
            
            try:
                log_time = datetime.strptime(parsed['timestamp'], '%Y-%m-%d %H:%M:%S')
                if log_time < cutoff_time:
                    continue
            except:
                continue
            
            total += 1
            level_counts[parsed['level']] += 1
            logger_counts[parsed['logger']] += 1
        
        return jsonify({
            'success': True,
            'stats': {
                'total': total,
                'by_level': dict(level_counts),
                'by_logger': dict(logger_counts)
            }
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@logs_bp.route('/clear', methods=['POST'])
def clear_logs():
    """Clear log file (admin only)"""
    try:
        if not os.path.exists(LOG_FILE):
            return jsonify({
                'success': True,
                'message': 'Log file not found'
            }), 200
        
        with open(LOG_FILE, 'w', encoding='utf-8') as f:
            f.write('')
        
        return jsonify({
            'success': True,
            'message': 'Logs cleared successfully'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
