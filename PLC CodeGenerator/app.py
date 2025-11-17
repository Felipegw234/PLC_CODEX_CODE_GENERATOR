"""
Servidor Web Flask para Gerador de Código PLC
Interface web para controle do PLC_CodeGenerator
"""

from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import os
from PLC_CodeGenerator import PLCCodeGenerator
import traceback

app = Flask(__name__)
CORS(app)

# Instância global do gerador
generator = PLCCodeGenerator()

@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html')

@app.route('/api/config', methods=['GET'])
def get_config():
    """Retorna configurações atuais"""
    try:
        return jsonify({
            'success': True,
            'type_mapping': generator.config.type_mapping,
            'suffix_mapping': generator.config.suffix_mapping,
            'pid_type_mapping': generator.config.pid_type_mapping
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/config', methods=['POST'])
def update_config():
    """Atualiza configurações"""
    try:
        data = request.json

        if 'type_mapping' in data:
            generator.config.type_mapping = data['type_mapping']

        if 'suffix_mapping' in data:
            generator.config.suffix_mapping = data['suffix_mapping']

        if 'pid_type_mapping' in data:
            generator.config.pid_type_mapping = data['pid_type_mapping']

        generator.config.save_config()

        return jsonify({
            'success': True,
            'message': 'Configurações salvas com sucesso'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/database/connect', methods=['POST'])
def connect_database():
    """Conecta ao banco de dados"""
    try:
        data = request.json
        server = data.get('server')
        database = data.get('database')
        username = data.get('username', None)
        password = data.get('password', None)

        if not server or not database:
            return jsonify({
                'success': False,
                'error': 'Servidor e banco de dados são obrigatórios'
            }), 400

        # Conecta ao banco
        success = generator.connect_database(server, database, username, password)

        if success:
            return jsonify({
                'success': True,
                'message': f'Conectado ao banco: {database}'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Falha ao conectar ao banco de dados'
            }), 500

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/api/database/status', methods=['GET'])
def database_status():
    """Verifica status da conexão"""
    try:
        connected = generator.db is not None and generator.db.connection is not None
        return jsonify({
            'success': True,
            'connected': connected
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/database/list-databases', methods=['POST'])
def list_databases():
    """Lista bancos de dados disponíveis no servidor"""
    try:
        data = request.json
        server = data.get('server')
        username = data.get('username', None)
        password = data.get('password', None)

        if not server:
            return jsonify({
                'success': False,
                'error': 'Servidor é obrigatório'
            }), 400

        # Cria string de conexão
        if username and password:
            conn_str = (
                f'DRIVER={{ODBC Driver 17 for SQL Server}};'
                f'SERVER={server};'
                f'DATABASE=master;'
                f'UID={username};'
                f'PWD={password}'
            )
        else:
            # Autenticação Windows
            conn_str = (
                f'DRIVER={{ODBC Driver 17 for SQL Server}};'
                f'SERVER={server};'
                f'DATABASE=master;'
                f'Trusted_Connection=yes;'
            )

        # Conecta ao servidor
        import pyodbc
        connection = pyodbc.connect(conn_str)
        cursor = connection.cursor()

        # Query para listar bancos de dados (excluindo bancos de sistema)
        query = """
            SELECT name
            FROM sys.databases
            WHERE name NOT IN ('master', 'tempdb', 'model', 'msdb')
            ORDER BY name
        """
        cursor.execute(query)

        databases = [row.name for row in cursor.fetchall()]

        cursor.close()
        connection.close()

        return jsonify({
            'success': True,
            'databases': databases,
            'server': server
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/api/database/phase-instances', methods=['GET'])
def list_phase_instances():
    """Lista Phase Instances disponíveis"""
    try:
        if not generator.db or not generator.db.connection:
            return jsonify({
                'success': False,
                'error': 'Não conectado ao banco de dados'
            }), 400

        cursor = generator.db.connection.cursor()

        # Query para listar Phase Instances
        query = """
            SELECT iID, sName_1
            FROM dbo.tblPhaseInstance
            ORDER BY sName_1
        """
        cursor.execute(query)

        phase_instances = [{'id': row.iID, 'name': row.sName_1} for row in cursor.fetchall()]
        cursor.close()

        return jsonify({
            'success': True,
            'phase_instances': phase_instances
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/api/generate/preview', methods=['POST'])
def generate_preview():
    """Gera preview dos códigos PLC com dados estruturados"""
    try:
        if not generator.db or not generator.db.connection:
            return jsonify({
                'success': False,
                'error': 'Não conectado ao banco de dados'
            }), 400

        data = request.json
        phase_instance_id = data.get('phase_instance_id', None)

        if not phase_instance_id:
            return jsonify({
                'success': False,
                'error': 'Phase Instance ID é obrigatório para o preview'
            }), 400

        # Busca ativações
        activations = generator.db.fetch_activations(phase_instance_id)

        if not activations:
            return jsonify({
                'success': False,
                'error': 'Nenhuma ativação encontrada para esta Phase Instance'
            }), 404

        # Agrupa ativações por step
        steps_data = {}
        for act in activations:
            if act.has_activation():
                suffix = generator.config.get_suffix(act.i_type, act.pid_type)

                # Pula ativação se deve ser desconsiderada (get_suffix retorna None)
                if suffix is None:
                    continue

                if act.step_no not in steps_data:
                    steps_data[act.step_no] = {
                        'step_no': act.step_no,
                        'step_name': act.step_name,
                        'activations': []
                    }

                tag_with_suffix = f"{act.tag_name}{suffix}"

                steps_data[act.step_no]['activations'].append({
                    'tag_name': act.tag_name,
                    'tag_with_suffix': tag_with_suffix,
                    'i_type': act.i_type,
                    'pid_type': act.pid_type
                })

        # Converte para lista ordenada
        steps_list = [steps_data[key] for key in sorted(steps_data.keys())]

        return jsonify({
            'success': True,
            'steps': steps_list,
            'total_steps': len(steps_list),
            'total_activations': sum(len(step['activations']) for step in steps_list)
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/api/generate', methods=['POST'])
def generate_code():
    """Gera códigos PLC"""
    try:
        if not generator.db or not generator.db.connection:
            return jsonify({
                'success': False,
                'error': 'Não conectado ao banco de dados'
            }), 400

        data = request.json
        output_dir = data.get('output_dir', 'output')
        phase_instance_id = data.get('phase_instance_id', None)
        controller_type = data.get('controller_type', 'all')  # 'rockwell', 'siemens', 'all'
        activation_conditions = data.get('activation_conditions', {})  # Condicionais por ativação

        # Cria diretório de saída
        os.makedirs(output_dir, exist_ok=True)

        # Busca ativações com filtro opcional
        activations = generator.db.fetch_activations(phase_instance_id)

        if not activations:
            return jsonify({
                'success': False,
                'error': 'Nenhuma ativação encontrada no banco de dados'
            }), 404

        # Converte chaves de step_no de string para int (JSON usa strings como chaves)
        activation_conditions_int = {}
        if activation_conditions:
            for step_no_str, step_data in activation_conditions.items():
                step_no = int(step_no_str)
                activation_conditions_int[step_no] = step_data

        # Gera arquivos
        files_generated = []

        # Gerar arquivos Rockwell
        if controller_type in ['rockwell', 'all']:
            # Rockwell Text
            ladder_text = generator.rockwell_gen.generate_text(activations, activation_conditions_int)
            ladder_file = os.path.join(output_dir, "rockwell_ladder.txt")
            with open(ladder_file, 'w', encoding='utf-8') as f:
                f.write(ladder_text)
            files_generated.append(ladder_file)

            # Rockwell L5X
            l5x_code = generator.rockwell_gen.generate_l5x(activations, activation_conditions_int)
            l5x_file = os.path.join(output_dir, "rockwell_ladder.L5X")
            with open(l5x_file, 'w', encoding='utf-8') as f:
                f.write(l5x_code)
            files_generated.append(l5x_file)

        # Gerar arquivo Siemens
        if controller_type in ['siemens', 'all']:
            # Siemens SCL (formato .txt)
            scl_code = generator.siemens_gen.generate_scl(activations, activation_conditions_int)
            scl_file = os.path.join(output_dir, "siemens_scl.txt")
            with open(scl_file, 'w', encoding='utf-8') as f:
                f.write(scl_code)
            files_generated.append(scl_file)

        return jsonify({
            'success': True,
            'message': 'Códigos gerados com sucesso',
            'activations_count': len(activations),
            'files': files_generated,
            'output_dir': os.path.abspath(output_dir),
            'controller_type': controller_type
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

@app.route('/api/download/<filename>', methods=['GET'])
def download_file(filename):
    """Download de arquivo gerado"""
    try:
        output_dir = request.args.get('output_dir', 'output')
        file_path = os.path.join(output_dir, filename)

        if not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'error': 'Arquivo não encontrado'
            }), 404

        return send_file(file_path, as_attachment=True)

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/preview/<filename>', methods=['GET'])
def preview_file(filename):
    """Preview do conteúdo de arquivo gerado"""
    try:
        output_dir = request.args.get('output_dir', 'output')
        file_path = os.path.join(output_dir, filename)

        if not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'error': 'Arquivo não encontrado'
            }), 404

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        return jsonify({
            'success': True,
            'filename': filename,
            'content': content
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/get-absolute-path', methods=['POST'])
def get_absolute_path():
    """Retorna o caminho absoluto de um diretório"""
    try:
        data = request.json
        relative_path = data.get('path', 'output')

        absolute_path = os.path.abspath(relative_path)

        return jsonify({
            'success': True,
            'absolute_path': absolute_path
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

if __name__ == '__main__':
    import socket

    # Tentar encontrar uma porta disponível
    def find_available_port(start_port=8080, max_attempts=10):
        for port in range(start_port, start_port + max_attempts):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                sock.bind(('', port))
                sock.close()
                return port
            except OSError:
                continue
        return None

    port = find_available_port()

    if port is None:
        print("ERRO: Nenhuma porta disponível encontrada!")
        print("Tente fechar outros programas e executar novamente.")
        input("\nPressione ENTER para sair...")
        exit(1)

    print("="*60)
    print("  GERADOR DE CÓDIGO LADDER E SCL - Interface Web")
    print("  Rockwell Studio 5000 | Siemens TIA Portal")
    print("="*60)
    print(f"\n🌐 Servidor iniciado com sucesso!")
    print(f"🌐 Acesse: http://localhost:{port}")
    print(f"🌐 Ou acesse: http://127.0.0.1:{port}")
    print("\n")

    try:
        app.run(debug=False, host='0.0.0.0', port=port, use_reloader=False)
    except KeyboardInterrupt:
        print("\n\n✓ Servidor encerrado com sucesso!")
    except Exception as e:
        print(f"\n\nERRO: {e}")
        input("\nPressione ENTER para sair...")
