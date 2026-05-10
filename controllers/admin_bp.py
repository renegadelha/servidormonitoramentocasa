from flask import *
import daofile
admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/removerdata')
def deletar_tuplas():
    #aqui eu removo todas as tuplas anterior a esta data
    dd = request.args.get('dd')
    mm = request.args.get('mm')
    aa = request.args.get('aa')

    resposta = daofile.remover_dados_antigos(f'{aa}-{mm}-{dd}')

    return f'qtde linhas removidas: {resposta}',200


@admin_bp.route('/remover')
def deletar_tuplas():
    dd = request.args.get('dd')
    mm = request.args.get('mm')
    aa = request.args.get('aa')

    resposta = daofile.remover_dados_antigos(f'{aa}-{mm}-{dd}')

    return f'qtde linhas removidas: {resposta}',200



@admin_bp.route('/removerabsurdo')
def deletar_tuplas():
    resposta = daofile.remover_temperaturas_absurdas(50)

    return f'qtde linhas removidas: {resposta}',200
