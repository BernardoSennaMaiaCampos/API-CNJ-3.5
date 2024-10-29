from flask import Flask, request, render_template, url_for, redirect
from datetime import datetime
import requests

from urllib.parse import urlencode, urlunparse

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False


@app.template_filter('format_date')
def format_date(value):
    if value:
        try:
            if "T" in value:
                date_obj = datetime.strptime(value, '%Y-%m-%dT%H:%M:%S')
            else:
                date_obj = datetime.strptime(value, '%Y-%m-%d')
            return date_obj.strftime('%d/%m/%Y')
        except (ValueError, TypeError):
            return value
    return value

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/resultado')
def resultado():
    pagina = request.args.get('pagina', 1, type=int)
    tribunal_filtro = request.args.get('tribunal')
    url = f"https://hcomunicaapi.cnj.jus.br/api/v1/comunicacao"
    

    

    params = {
        'siglaTribunal': request.args.get('tribunal'),
        'numeroOab': request.args.get('numero_oab'),
        'ufOab': request.args.get('uf_oab'),
        'nomeAdvogado': request.args.get('nome_advogado'),
        'nomeParte': request.args.get('nome_parte'),
        'numeroProcesso': request.args.get('numero_processo'),
        'dataDisponibilizacaoInicio': request.args.get('data_inicio'),
        'dataDisponibilizacaoFim': request.args.get('data_fim'),
        'pagina': pagina,
        'itensPorPagina': 10
    }
    print(params)
    
    if tribunal_filtro and tribunal_filtro != "null":
        params['siglaTribunal'] = tribunal_filtro
    
    try:
        proxy = {'http': None, 'https': None}
        response = requests.get(url, proxies=proxy, params=params, timeout=180)
        response.raise_for_status()
        response.encoding = 'utf-8'
        resultado = response.json()
        print(resultado)
        processos = []
        
        if 'items' in resultado:
            for item in resultado['items']:
                destinatarios = []
                if 'destinatarios' in item:
                    for destinatario in item['destinatarios']:
                        destinatario_info = {
                            'nome': destinatario.get('nome'),
                            'polo': destinatario.get('polo'),
                        }
                        destinatarios.append(destinatario_info)
                        
                def safe_str(value):
                    if value is None or value == "":
                        return "Informação não disponível"  
                
                    if isinstance(value, str):
                        
                        try:
                            value = value.encode('latin1').decode('utf-8')
                        except (AttributeError, UnicodeDecodeError, UnicodeEncodeError):
                            pass
                        
                        
                        try:
                            if "T" in value:  
                                date_obj = datetime.strptime(value, '%Y-%m-%dT%H:%M:%S')
                            elif ' ' in value and len(value.split(' ')[1]) == 8:  
                                date_obj = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
                            else:
                                return value  
                            
                            return date_obj.strftime('%d/%m/%Y %H:%M:%S')  
                
                        except ValueError:
                            return value  
                
                    return value


                destinatario_advogados = []
                if 'destinatarioadvogados' in item:
                    for destinatarioadvogado in item['destinatarioadvogados']:
                        print("Valor bruto de CriadoEm:", destinatarioadvogado.get('created_at'))
                        print("Valor bruto de AtualizadoEm:", destinatarioadvogado.get('updated_at'))
                        advogado_info = {
                            'Id': safe_str(destinatarioadvogado.get('id')),
                            'ComunicacaoId': safe_str(destinatarioadvogado.get('comunicacao_id')),
                            'AdvogadoId': safe_str(destinatarioadvogado.get('advogado_id')),
                            'CriadoEm': safe_str(destinatarioadvogado.get('created_at')),
                            'AtualizadoEm': safe_str(destinatarioadvogado.get('updated_at')),
                            'Advogado': {
                                'Nome': safe_str(destinatarioadvogado.get('advogado', {}).get('nome')),
                                'NumeroOab': safe_str(destinatarioadvogado.get('advogado', {}).get('numero_oab')),
                                'UfOab': safe_str(destinatarioadvogado.get('advogado', {}).get('uf_oab'))
                            }
                        }
                        destinatario_advogados.append(advogado_info)
                else:
                    destinatario_advogados = None

                processo = {
                    'ID': safe_str(item.get('id')),
                    'DataDisponibilizacao': safe_str(item.get('data_disponibilizacao')),
                    'SiglaTribunal': safe_str(item.get('siglaTribunal')),
                    'TipoComunicacao': safe_str(item.get('tipoComunicacao')),
                    'NomeOrgao': safe_str(item.get('nomeOrgao')),
                    'Texto': safe_str(item.get('texto')),
                    'NumeroProcesso': safe_str(item.get('numero_processo')),
                    'Meio': safe_str(item.get('meio')),
                    'Link': safe_str(item.get('link')) or 'Indisponível', 
                    'TipoDocumento': safe_str(item.get('tipoDocumento')),
                    'NomeClasse': safe_str(item.get('nomeClasse')),
                    'NumeroComunicacao': safe_str(item.get('numeroComunicacao')),
                    'DataDeEnvio': safe_str(item.get('dataenvio')),
                    'destinatarios': safe_str(destinatarios),  
                    'destinatario_advogados': safe_str(destinatario_advogados)  
                }
                processos.append(processo)

        total_items = resultado.get('count', 0)
        itens_por_pagina = 10
        total_paginas = (total_items // itens_por_pagina) + (1 if total_items % itens_por_pagina else 0)

        return render_template(
            'resultado.html', 
            processos=processos, 
            pagina=pagina, 
            total_paginas=total_paginas
        )
    
    except requests.Timeout:
        print("Houve Timeout")
        MensagemDeErro = "A requisição demorou demais para responder. Tente novamente mais tarde."
        return render_template('resultado.html', MensagemDeErro=MensagemDeErro)


    except requests.RequestException as erro:
        
        MensagemDeErro="Infelizmente a API do CNJ está fora do ar. Isso impossibilita que as buscas sejam realizadas no momento. A estabilidade da API é de responsabilidade do CNJ, não sendo possível por nós, CTEC, dizer precisamente em que momento voltará. Mas fique tranquilo, normalmente não demora mais do que 1 dia. Enquanto isso, talvez lhe seja interessante usar alguns de nossos outros sistemas. Clique no sistema de sua escolha para ser imediatamente direcionado para ele:<br><br><a href='http://pgmtotal.pgm.rio.rj.gov.br/spotpgm/' class='MensagemDeErro' class='LinksErro>SpotPGM</a><br><a href='http://pgmtotal.pgm.rio.rj.gov.br/certidoes/' class='MensagemDeErro LinksErro'>RGI-Search</a><br><a href='http://pesquisa.pgm.rio.rj.gov.br/entrar?redirect=c5976abd41be2e50619cfa6bd37544c7511886140ed65fca73b852a4eaaa437d28a387d8bb0d454e88102924cdb7fcd1445f' class='MensagemDeErro' class='LinksErro'>LexLupa</a><br><a href='http://pgmtotal.pgm.rio.rj.gov.br/intranet_nova/pgm-receitas/' class='MensagemDeErro' class='LinksErro'>PGM-Receita Federal</a>"
        
        return render_template('resultado.html', MensagemDeErro=MensagemDeErro, erro=f"Erro {erro}")

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
