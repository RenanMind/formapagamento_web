from flask import Flask, render_template, request, send_file, abort
from datetime import datetime
import os, io
from pdfrw import PdfReader, PdfWriter, PdfDict, PdfName, PdfObject


app = Flask(__name__)

TEMPLATE_PATH = "Template.pdf"
PASTA_SAIDA = "gerados"

LIFE_PLANNERS = {
    "Luiz Felipe da Silva Martins": {"cpd": "166025", "ponto": "Black Belt"},
    "Humberto Mandaro Neto": {"cpd": "174227", "ponto": "Black Belt"},
    "Carolina Martins Magalhaes": {"cpd": "196634", "ponto": "Black Belt"},
    "Ellen Marques Penna": {"cpd": "276469", "ponto": "Black Belt"},
    "Bruno da Silva Raso": {"cpd": "173260", "ponto": "Black Belt"},
    "Isabella Martins Cassani": {"cpd": "199182", "ponto": "Black Belt"},
    "Daniel Carvalho Maini": {"cpd": "194076", "ponto": "Black Belt"},
    "Rafael Martins Waddington": {"cpd": "241349", "ponto": "Black Belt"},
    "Raphael Ferreira Costa": {"cpd": "170340", "ponto": "Black Belt"},
    "Júlia Ferreira Lima Biscaia": {"cpd": "239301", "ponto": "Black Belt"},
    "Rafael Campos Marinho": {"cpd": "266296", "ponto": "Black Belt"},
    "Bruna Passos Garrido": {"cpd": "258897", "ponto": "Black Belt"},
    "Rafael Fernandes Reis": {"cpd": "174243", "ponto": "Fenix"},
    "Raphael Garcia Barreto": {"cpd": "141689", "ponto": "Fenix"},
    "Bernardo de Barros Ballian": {"cpd": "174938", "ponto": "Fenix"},
    "Debora Alessandra Costa Cavalcante": {"cpd": "253849", "ponto": "Fenix"},
    "Mariana Fiorani de Almeida Magalhães": {"cpd": "124644", "ponto": "Fenix"},
    "Michelle Lopes": {"cpd": "135079", "ponto": "Fenix"},
    "Luciana Rocha": {"cpd": "108076", "ponto": "Fenix"},
    "Mariana Costa Maia Gouvea": {"cpd": "235572", "ponto": "Fenix"},
    "Adriana Villardo": {"cpd": "118752", "ponto": "Fenix"},
    "Romulo Oliveira Carvalho Cavalcanti ": {"cpd": "169367", "ponto": "Fenix"},
    "Renan Marques Laterza": {"cpd": "208918", "ponto": "Fenix"},
    "Luiz Felipe da Silva Castro": {"cpd": "154229", "ponto": "Fenix"},
    "Kaian Raia Pagan": {"cpd": "244939", "ponto": "Fenix"},
}

LP_CPDS = {nome: dados["cpd"] for nome, dados in LIFE_PLANNERS.items()}
LP_PONTOS = {nome: dados["ponto"] for nome, dados in LIFE_PLANNERS.items()}


def gerar_data_formatada():
    meses = [
        "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
    ]
    hoje = datetime.today()
    return f"Rio de Janeiro, {hoje.day} de {meses[hoje.month - 1]} de {hoje.year}"


def preencher_pdf(dados, saida_path):
    pdf = PdfReader(TEMPLATE_PATH)
    for pagina in pdf.pages:
        if pagina.Annots:
            for campo in pagina.Annots:
                if campo.Subtype == '/Widget' and campo.T:
                    chave = campo.T[1:-1]
                    if chave in dados:
                        valor = dados[chave]
                        campo.V = PdfName(valor.replace('/', '')) if valor.startswith('/') else PdfObject(f'({valor})')
                        campo.AS = campo.V
                        campo.AP = None
    PdfWriter().write(saida_path, pdf)


@app.route("/")
def index():
    black_belts = [nome for nome, d in LIFE_PLANNERS.items() if d['ponto'] == 'Black Belt']
    fenix = [nome for nome, d in LIFE_PLANNERS.items() if d['ponto'] == 'Fenix']
    return render_template("index.html", black_belts=black_belts, fenix=fenix)


@app.route("/gerar", methods=["POST"])
def gerar():
    nome = request.form.get("nome", "").strip()
    cpf = request.form.get("cpf", "").strip()
    apolice = request.form.get("apolice", "").strip()
    lp_nome = request.form.get("lp", "").strip()
    pagamento = request.form.get("pagamento", "").strip()

    if not nome or not lp_nome or pagamento == "Selecione...":
        return abort(400, "Preencha todos os campos obrigatórios")

    data_formatada = gerar_data_formatada()

    opcoes = request.form.getlist("opcoes")
    dados = {
        "opcao-emissao": "/Yes" if "Emissao" in opcoes else "/Off",
        "opcao-processos": "/Yes" if "Processos Operacionais" in opcoes else "/Off",
        'nome-do-segurado': nome,
        'cpf': cpf,
        'N apólice POB1': apolice,
        'nome-do-life-planner': lp_nome,
        'Código cpd': LP_CPDS.get(lp_nome, ""),
        'Código agência': LP_PONTOS.get(lp_nome, ""),
        'Local e data': data_formatada,
        'Local e data2': data_formatada,
    }

    if pagamento == 'Boleto':
        dados['Outros p1'] = 'BOLETO'
        dados['forma-de-pagamento'] = '3'

    elif pagamento == 'Cartão de Crédito':
        dados['forma-de-pagamento'] = '2'
        dados['Titular-cartao'] = request.form.get("titular", "")
        dados['Administradora'] = request.form.get("adm", "")
        numero = request.form.get("numero", "").replace(" ", "")
        for i, digito in enumerate(numero):
            dados[str(i + 1)] = digito
        validade = request.form.get("validade", "").split("/")
        if len(validade) == 2:
            dados['validade-mes'] = validade[0]
            dados['validade-ano'] = validade[1]

    elif pagamento == 'Conta para Débito':
        dados['forma-de-pagamento'] = '1'
        dados['Nome do banco'] = request.form.get("banco", "")
        dados['N do banco'] = request.form.get("nbanco", "")
        dados['Agência com dígito'] = request.form.get("agencia", "")
        dados['Contacorrente com dígito'] = request.form.get("conta", "")
        dados['Nome-do-correntista'] = request.form.get("correntista", "")

    if not os.path.exists(PASTA_SAIDA):
        os.makedirs(PASTA_SAIDA)

    saida_path = os.path.join(PASTA_SAIDA, f"FormaPagamento_{nome}.pdf")
    preencher_pdf(dados, saida_path)
    return send_file(saida_path, as_attachment=True)


@app.route("/healthz")
def healthz():
    return {"status": "ok"}, 200


if __name__ == '__main__':
    debug_mode = os.environ.get("FLASK_DEBUG", "false").lower() == "true"
    app.run(debug=debug_mode)
