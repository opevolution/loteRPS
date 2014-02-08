# -*- coding: utf-8 -*-
################################################################################
#                                                                              #
# Alexandre Defendi - Evoluir Informatica  - Open Evolution                    #
#                                                                              #
# Módulo de Exportação de Lote de RPS                                          #
#                                                                              #
# This program is free software: you can redistribute it and/or modify         #
# it under the terms of the GNU Affero General Public License as published by  #
# the Free Software Foundation, either version 3 of the License, or            #
# (at your option) any later version.                                          #
#                                                                              #
# This program is distributed in the hope that it will be useful,              #
# but WITHOUT ANY WARRANTY; without even the implied warranty of               #
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the                #
# GNU Affero General Public License for more details.                          #
#                                                                              #
# You should have received a copy of the GNU Affero General Public License     #
# along with this program.  If not, see <http://www.gnu.org/licenses/>.        #
#                                                                              #
# versão do módulo : 0.0.1                                                     #
# versao do arquivo: 0.0.1  04/02/2014                                         #
################################################################################

from lxml import etree
from osv import fields, osv

CABECALHO_XML = '<?xml version="1.0"?>'

class loterps(osv.osv):
    """Lote de Recibo Provisório de Serviços"""

    _name = 'loterps'
    
    def gera_arquivo_xml(self, cr, uid, invoice_ids, context=None):
        """
        Função que gera o arquivo xml para exportar
        @param self: Ponteiro do Objeto
        @param cr: Linha atual do cursor do Banco de Dados,
        @param uid: Usuário atual para controle de acesso,
        @param invoice_ids: Lista dos Invoices contida no lote
        @param context: Um dicionário padrão para valores contextuais
        @return : Arquivo.
        """
        
        EnviarLote = etree.XML("<EnviarLoteRpsEnvio></EnviarLoteRpsEnvio>")
        loteRps    = etree.XML("<LoteRps><NumeroLote/><Cnpj/><InscricaoMunicipal/><QuantidadeRps/></LoteRps>")
        ListaRps   = etree.XML("<ListaRps></ListaRps>")
        Rps        = etree.XML("<Rps></Rps>")
        InfRps     = etree.XML("<InfRps><DataEmissao/><NaturezaOperacao/><RegimeEspecialTributacao/><OptanteSimplesNacional/><IncentivadorCultural/><Status/></InfRps>")
        IdentRps   = etree.XML("<IdentificacaoRps><Numero/><Serie/><Tipo/></IdentificacaoRps>")
        
        
        
        res = {'arquivo': None}
        return res
        
    def limpa_cnpj(self, cnpj):
        res = cnpj.replace(".","")
        res = cnpj.replace("/","")
        res = cnpj.replace("-","")
        return res
        

    _columns = {
                'name' : fields.char(u'Número do Lote de RPS', size=4),
                'data_in': fields.date(u'Data da Criação'),
                'data_out': fields.date(u'Data de Geração'),
                'state': fields.selection([
                                           ('draft', 'Novo'),
                                           ('done', 'Gerado'),
                                           ('cancel','Cancelado')
                                           ]),
                }
loterps()