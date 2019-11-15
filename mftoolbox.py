import sys
import configparser
import datetime
import os
import zeep
import xml.etree.ElementTree as ET


def encoding():
    # define no encoding baseado no sistema operacional
    # arquivo em Windows (win32) tem que ser salvo em Unicode
    # se for Mac (darwin) tem que ser salvo como UTF-8
    str_platform = sys.platform
    if str_platform == 'win32':
        return 'utf_16'
    elif str_platform == 'darwin':
        return 'utf_8'
    del str_platform


class Build:
    """
    O controle de build é feito através da data e hora em que o arquivo do Magic Formula foi salvo pela última vez.
    Se a data do arquivo for mais recente do que está registrado no controle de build, o número do build
        será incrementado em 1.
    Se o arquivo de build ainda não existir, será criado com o nome da versão atual (hardcoded), build=0, data de
        atualização = data que o arquivo do Magic Formula foi salvo pela última vez.
    Se o arquivo de build existir e já houver uma entrada para o nome da versão atual, compara o horário da última
        gravação do Magic Formula. Se a última gravação for mais recente do que o registro no controle de build,
        este será incrementado em 1.
    Se o arquivo de build existir e não houver uma entrada para o nome da versão atual, esta será criada com
        o nome da versão atual (hardcoded), build=0, data de atualização = data que o arquivo do Magic Formula
        foi salvo pela última vez.
    07/10/19: controle para definir build diferente por data apenas ou por data e hora. 0 para data e 1 para data e hora
    """
    def __init__(self, VersaoAtual, FileName, Controle):

        self.str_versao_atual = VersaoAtual
        self.str_nome_arquivo_build = 'BuildHistory.txt'
        self.str_encoding = encoding()
        self.str_nome_arquivo_chamada = FileName

        # data em que o arquivo atual foi salvo
        self.dtt_ultima_atualizacao = os.stat(os.path.basename(FileName)).st_mtime

        # cria se não existe o arquivo com os dados do build atual, senão, abre o arquivo existente
        if not os.path.isfile(self.str_nome_arquivo_build):
            dic_build_content = configparser.ConfigParser()
            dic_build_content[self.str_versao_atual] = {'build': '0',
                                                   'atualização': str(self.dtt_ultima_atualizacao),
                                                   'data': datetime.datetime.fromtimestamp(
                                                       self.dtt_ultima_atualizacao).strftime('%d-%m-%Y %H:%M:%S')}

            with open(self.str_nome_arquivo_build, 'w', encoding=self.str_encoding) as fil_build:
                dic_build_content.write(fil_build)
                fil_build.close()
        else:
            dic_build_content = configparser.ConfigParser()
            dic_build_content.read(self.str_nome_arquivo_build, encoding=self.str_encoding)

        # se não houver entrada para a versão atual, cria (anexando ao arquivo existente)
        # Se houver, verifica se os dados do build são iguais
        try:
            self.int_numero_build = dic_build_content.getint(self.str_versao_atual, 'build')
            flt_atualizacao = dic_build_content.getfloat(self.str_versao_atual, "atualização")
            self.str_data_build = datetime.datetime.fromtimestamp(self.dtt_ultima_atualizacao).strftime('%d-%m-%Y %H:%M:%S')

            # se a data da última revisão do arquivo for diferente da informação do arquivo de build, aumenta o número do build
            # e atualiza o arquivo de controle de build
            if (self.dtt_ultima_atualizacao != flt_atualizacao and Controle == 1) or (datetime.datetime.fromtimestamp(self.dtt_ultima_atualizacao).strftime('%d-%m-%Y') != datetime.datetime.fromtimestamp(flt_atualizacao).strftime('%d-%m-%Y') and Controle == 0):
                self.int_numero_build = self.int_numero_build + 1
                dic_build_content.set(self.str_versao_atual, 'build', str(self.int_numero_build))
                dic_build_content.set(self.str_versao_atual, 'atualização', str(self.dtt_ultima_atualizacao))
                dic_build_content.set(self.str_versao_atual, 'data',
                                      datetime.datetime.fromtimestamp(self.dtt_ultima_atualizacao).strftime(
                                          '%d-%m-%Y %H:%M:%S'))
                # sobrescreve o arquivo
                with open(self.str_nome_arquivo_build, 'w+', encoding=self.str_encoding) as fil_build:
                    dic_build_content.write(fil_build)
                fil_build.close()
        except:
            self.int_numero_build = 0
            dic_build_content = configparser.ConfigParser()
            dic_build_content[self.str_versao_atual] = {'build': self.int_numero_build,
                                                   'atualização': str(self.dtt_ultima_atualizacao),
                                                   'data': datetime.datetime.fromtimestamp(
                                                       self.dtt_ultima_atualizacao).strftime('%d-%m-%Y %H:%M:%S')}
            # adiciona ao que já está no arquivo
            with open(self.str_nome_arquivo_build, 'a', encoding=self.str_encoding) as fil_build:
                dic_build_content.write(fil_build)
            fil_build.close()

        self.str_ultima_atualizacao = datetime.datetime.fromtimestamp(self.dtt_ultima_atualizacao).strftime(
            '%d-%m-%Y %H:%M:%S')
        self.txt_int_numero_build = str(self.int_numero_build)
"""
        try:
            del dic_build_content
            del fil_build
            del flt_atualizacao
        except:
            pass
"""
class UltimaCotacaoDolar:

    # Documentação de apoio:
    #
    #   http://catalogo.governoeletronico.gov.br/arquivos/Documentos/WS_SGS_BCB.pdf - descrição do uso do Webservice
    #   http://python-zeep.readthedocs.io/en/master/ - zeep, biblioteca para trabalhar com webservices
    #   http://blog.tiagocrizanto.com/configuracoes-do-webservice-do-banco-central-cotacoes-diversas/

    def __init__(self):
        wsdl='https://www3.bcb.gov.br/sgspub/JSP/sgsgeral/FachadaWSSGS.wsdl'
        # 07/11/19: nome da variável alterado de cliente para zzz.
        # por algum motivo, passou a dar erro depois do upgrade para 3.8.0
        try:
            zzz=zeep.client.Client(wsdl=wsdl)
            xml_response = zzz.service.getUltimoValorVO(1).ultimoValor  # o 1 é o código da série temporal Dólar
            self.valor = xml_response.valor._value_1
            self.data = datetime.date(xml_response.ano, xml_response.mes, xml_response.dia)
            self.erro = False
        except:
            self.valor=0
            self.data = datetime.date(datetime.datetime.now().year, datetime.datetime.now().month, datetime.datetime.now().day)
            self.erro = True

class Proventos:

    #
    # Define a classe Proventos
    # Autor: Celso Oliveira (c.oliveira@live.com)
    # Controle de versão:
    #
    #   1.0, 16/Ago/18, criação.
    #
    # Documentação de apoio:
    #
    #   http://catalogo.governoeletronico.gov.br/arquivos/Documentos/WS_SGS_BCB.pdf - descrição do uso do Webservice
    #   http://python-zeep.readthedocs.io/en/master/ - zeep, biblioteca para trabalhar com webservices
    #   http://blog.tiagocrizanto.com/configuracoes-do-webservice-do-banco-central-cotacoes-diversas/

    def __init__(self, arg_idioma, arg_cd_acao, arg_data, arg_valor, arg_tipo, arg_referencia):
        self.idioma = arg_idioma
        self.cd_acao = arg_cd_acao
        self.arg_data = arg_data
        self.arg_valor = arg_valor
        self.arg_tipo = arg_tipo
        self.tipo = self.arg_tipo.upper()
        self.referencia = arg_referencia
        self.data = datetime.datetime(int(self.arg_data[6:]),int(self.arg_data[3:5]),int(self.arg_data[:2]))
        self.ano = self.data.year
        self.mes = self.data.month
        self.dia = self.data.day
        if self.idioma == "ENG": self.valor=float(self.arg_valor)
        elif self.idioma == "PTB": self.valor=float(self.arg_valor.replace('.','').replace(',','.'))
        #Normalizando o tipo de dividendo
        #tipos existentes nas bases da Fundamentus:
        #"JUROS"
        #"JRS CAP PROPRIO"
        #"JRS CAP PRÓPRIO"
        #"DIVIDENDO"
        #"REST CAP DIN"
        #"JUROS MENSAL"
        #"RESTITUIÃ§Ã£O DE CAPITAL"
        #"DIVIDENDO MENSAL"
        #Fundamentus não apresenta dados de bonificações
        if self.tipo[:1] == "J": self.tipo_normalizado = "JCP"
        if self.tipo[:1] == "D": self.tipo_normalizado = "DIV"
        if self.tipo[:1] == "R": self.tipo_normalizado = "RST"

class Timestamp:
    """
    horário da execução
    """
    def __init__(self):

        dtt_now = datetime.datetime.now()
        self.str_yyyymmdd = dtt_now.strftime('%Y%m%d')
        self.str_hhmmss = dtt_now.strftime('%H%M%S')
        self.dtt_timestamp = dtt_now.timestamp()
        self.dtt_now = dtt_now

class CotacaoDolarData:
    def __init__(self, arg_data):
        self.data = datetime.datetime.strptime(arg_data,'%d/%m/%Y')
        wsdl = 'https://www3.bcb.gov.br/sgspub/JSP/sgsgeral/FachadaWSSGS.wsdl'
        cliente = zeep.client.Client(wsdl=wsdl)
        xml_response = cliente.service.getValor(1,arg_data)  # o 1 é o código da série temporal Dólar
        self.valor = xml_response._value_1

class CotacaoDolarHistorico:
    #ideias para chegar à solução vieram de vários sites:
    #https://python-zeep.readthedocs.io/en/master/datastructures.html
    #https://stackoverflow.com/questions/1130819/how-to-create-arraytype-for-wsdl-in-python-using-suds
    #depois fiquei testando no prompt até conseguir montar um objeto que funcionasse
    def __init__(self, arg_data_inicio, arg_data_fim):
        self.data_inicio = datetime.datetime.strptime(arg_data_inicio, '%d/%m/%Y')
        self.data_fim = datetime.datetime.strptime(arg_data_fim, '%d/%m/%Y')
        STR_WSDL = 'https://www3.bcb.gov.br/sgspub/JSP/sgsgeral/FachadaWSSGS.wsdl'
        OBJ_CLIENTE = zeep.client.Client(wsdl=STR_WSDL)
        OBJ_FACTORY = OBJ_CLIENTE.type_factory('ns0')
        OBJ_ARRAYOFFLONG = OBJ_FACTORY.ArrayOfflong([1])
        XML_RESPONSE = OBJ_CLIENTE.service.getValoresSeriesXML(OBJ_ARRAYOFFLONG, arg_data_inicio, arg_data_fim)
        XML_ROOT = ET.fromstring(XML_RESPONSE._value_1)
        lst_resultado = []
        for xml_element in XML_ROOT[0]:
            lst_resultado.append([xml_element[0].text, xml_element[1].text])
        self.cotacoes = lst_resultado
        self.itens = len(lst_resultado)