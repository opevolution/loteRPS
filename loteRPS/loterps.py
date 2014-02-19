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

import logging
import base64
import unicodedata
import time
from lxml import etree
from copy import deepcopy
from osv import fields, osv

CABECALHO_XML = '<?xml version="1.0"?>'

_logger = logging.getLogger(__name__)
Log = True 

def somente_ascii(valor):
    '''
    Usado como decorator para a nota fiscal eletrônica de servicos
    '''
    
    ant = unicode(valor)
    
    ret = unicodedata.normalize('NFD', ant).encode('ascii', 'ignore')
    
    _logger.info("ASCII: "+str(ret))
    
    return ret

def converte_valor_xml(valor):
    
    ret = '0.00'

    if isinstance(valor, float) or isinstance(valor, int):
        try:
            ret = "%.2f" % valor
        except ValueError:
            pass
    return ret
        
def limpa_cnpj_cpf(cnpj):
    res = cnpj.replace(".","")
    res = res.replace("/","")
    res = res.replace("-","")
    return res

def recursively_empty(e):
    if e.text:
        return False
    return all((recursively_empty(c) for c in e.iterchildren()))

class loterps(osv.osv):
    """Lote de Recibo Provisório de Serviços"""

    _name = 'loterps'

#     def create_sequence(self, cr, uid, vals, context=None):
#         seq = {
#             'name': vals['name'],
#             'implementation': 'no_gap',
#             'padding': 1,
#             'number_increment': 1}
#         if 'company_id' in vals:
#             seq['company_id'] = vals['company_id']
#         return self.pool.get('ir.sequence').create(cr, uid, seq)


    def gera_id(self, cr, uid, id, context=None):
        this = self.browse(cr, uid, id)
        if context is None:
            context = {}

        res = False
        if not this.company_id:
            stErro = u'Selecione a empresa prestadora para poder emitir a RPS.'
            raise osv.except_osv(
                _('Error !'), ("Error Validating RPS:\n '%s'") % (stErro, ))
        else:
            if Log:
                _logger.info("Empresa ID: "+str(this.company_id.id))
            empresa = self.pool.get('res.company').browse(cr, uid, this.company_id.id, context=context)
            if not empresa.rps_sequence_id:
                raise osv.except_osv(u'A RPS deve ter uma sequencia interna')
            else:
                if Log:
                    _logger.info("Gerar a sequencia ID:"+str(empresa.rps_sequence_id.id))
                obj_seq = self.pool.get('ir.sequence')
                c = {}
                res = obj_seq.next_by_id(cr, uid, empresa.rps_sequence_id.id, context=c)
                
        return res    
    
    def anexarRps(self,cr,uid,id,conteudo,nome,context={}):
        if Log:
            _logger.info("Anexando RPS:" + conteudo)
        attach_id=self.pool.get('ir.attachment').create(cr, uid, {
                                                'name': nome,
                                                'datas': base64.encodestring(conteudo),
                                                'datas_fname': nome,
                                                'res_model': 'loterps',
                                                'res_id': id,
                                                }, context=context)
        return True

    def gera_arquivo_xml(self, cr, uid, id, nrVlLote, context=None):
        """
        Função que gera o arquivo xml para exportar
        @param self: Ponteiro do Objeto
        @param cr: Linha atual do cursor do Banco de Dados,
        @param uid: Usuário atual para controle de acesso,
        @param invoice_ids: Lista dos Invoices contida no lote
        @param context: Um dicionário padrão para valores contextuais
        @return : Arquivo.
        """
        def preenche(tree,context):
            for child in tree:
                tag = child.tag
                valor = context.get(tag)
                if valor is not None:
                    if Log:
                        _logger.info("preenche child: "+str(tag)+" text: "+str(valor))
                    child.text = str(valor)

        if context is None:
            context = {}
         
        var = {}

        if Log:
            _logger.info("Numero Lote: "+str(nrVlLote))
        try:
            nrVlLote = int(nrVlLote)
        except ValueError:
            nrVlLote = 0   
#         if not isinstance( nrVlLote, ( int, long ) ):
#             if Log:
#                 _logger.info("Numero Lote nao é um inteiro")
#             nrVlLote = 0
    
        this = self.browse(cr, uid, id)
          
        empresa   = self.pool.get('res.company').browse(cr, uid, this.company_id.id, context=context)
        mypartner = self.pool.get('res.partner').browse(cr, uid, empresa.partner_id.id, context=context)
        
        MyCidadeCode = mypartner.l10n_br_city_id.state_id.ibge_code+mypartner.l10n_br_city_id.ibge_code
       
        tpFiscal  = self.pool.get('l10n_br_account.partner.fiscal.type').browse(cr, uid, mypartner.partner_fiscal_type_id.id, context=context)
         
        if tpFiscal.code == 'Simples Nacional':
            vlTpFiscal = '1'
        else:
            vlTpFiscal = '2'
         
        if Log:
            _logger.info("Simples Nacional: "+vlTpFiscal)
         
        EnviarLote = etree.XML("<EnviarLoteRpsEnvio></EnviarLoteRpsEnvio>")
        loteRps    = etree.XML("<LoteRps><NumeroLote/><Cnpj/><InscricaoMunicipal/><QuantidadeRps/></LoteRps>")
        ListaRps   = etree.XML("<ListaRps></ListaRps>")
        Rps        = etree.XML("<Rps></Rps>")
        InfRps     = etree.XML("<InfRps><DataEmissao/><NaturezaOperacao/><RegimeEspecialTributacao/><OptanteSimplesNacional/><IncentivadorCultural/><Status/></InfRps>")
        IdentRps   = etree.XML("<IdentificacaoRps><Numero/><Serie/><Tipo/></IdentificacaoRps>")
        Servico    = etree.XML("<Servico><ItemListaServico/><Discriminacao/><CodigoMunicipio/></Servico>")
        ValServ    = etree.XML("<Valores><ValorServicos/><ValorDeducoes/><ValorPis/><ValorCofins/><ValorInss/><ValorIr/><ValorCsll/><IssRetido/><ValorIss/><ValorIssRetido/><OutrasRetencoes/><BaseCalculo/><ValorLiquidoNfse/><DescontoIncondicionado/><DescontoCondicionado/></Valores>")
        Prestad    = etree.XML("<Prestador><Cnpj/><InscricaoMunicipal/></Prestador>")
        Tomador    = etree.XML("<Tomador><RazaoSocial/></Tomador>")

        ideToma    = etree.XML("<IdentificacaoTomador></IdentificacaoTomador>")
        CNPToma    =  etree.XML("<CpfCnpj><Cpf/><Cnpj/></CpfCnpj>")
        EndToma    = etree.XML("<Endereco><Endereco/><Numero/><Complemento/><Bairro/><CodigoMunicipio/><Uf/><Cep/></Endereco>")


        conToma    = etree.XML("<Contato><Telefone/><Email/></Contato>")

         
        loteRps.append( ListaRps )
        EnviarLote.append( loteRps )
        
        if Log:
            _logger.info("1") 
        objInvoice = self.pool.get('account.invoice')
        if Log:
            _logger.info("Invoice IDs:"+str(this.invoice_ids))
        qtdeRPS = 0
        for invId in this.invoice_ids:
            qtdeRPS = qtdeRPS + 1     # acumula a quantidade de RPS lido
            
            if Log:
                _logger.info("Invoice ID:"+str(invId.id))
            invoice = objInvoice.browse(cr, uid, invId.id, context=context)    # browse  a fatura
            if Log:
                _logger.info(str(invoice.name))
             
            idLine = invoice.invoice_line[0]
            if Log:
                _logger.info("Invoice Line ID: "+str(idLine.id))
            LinhaInv = self.pool.get('account.invoice.line').browse(cr, uid, idLine.id, context=context)  

            ServId = LinhaInv.product_id
            if Log:
                _logger.info("Servico ID: "+str(ServId.id))
            ServInv = self.pool.get('product.product').browse(cr, uid, ServId.id, context=context)
            if Log:
                _logger.info("Servico: "+str(ServId.name))
           
            iTpServ = self.pool.get('l10n_br_account.service.type').browse(cr, uid, ServInv.service_type_id.id, context=context)
           
            partner  = self.pool.get('res.partner').browse(cr, uid, invoice.partner_id.id, context=context)
            CidadeCode = partner.l10n_br_city_id.state_id.ibge_code+partner.l10n_br_city_id.ibge_code
            
            pFiscal  = self.pool.get('account.fiscal.position').browse(cr, uid, invoice.fiscal_position.id, context=context)
            
            
            cpRps    = deepcopy(Rps)
            cpInfRps = deepcopy(InfRps)
            cpIdentRps = deepcopy(IdentRps)
            cpServico  = deepcopy(Servico)
            cpValServ  = deepcopy(ValServ)
            cpPrestad  = deepcopy(Prestad)
            cpTomador  = deepcopy(Tomador)
            cpEndToma  = deepcopy(EndToma)

            cpIdeToma  = deepcopy(ideToma)
            cpCNPToma  = deepcopy(CNPToma)
            cpEndToma  = deepcopy(EndToma)
            cpConToma  = deepcopy(conToma)

            
            cpInfNFSE = {
                    'DataEmissao'               : str(invoice.date_invoice or ''),
                    'NaturezaOperacao'          : str(pFiscal.code or ''),
                    'OptanteSimplesNacional'    : vlTpFiscal,
                    'IncentivadorCultural'      : '2',
                    'Status'                    : '1',
                    } 
            preenche(cpInfRps, cpInfNFSE)
            
            cpIdentNFSE = {
                           'Numero': invoice.internal_number or '',
                           'Serie': '',
                           'Tipo': '1',
                           }

            preenche(cpIdentRps, cpIdentNFSE)

            cpServicoNFSE = {
                           'ItemListaServico': str(iTpServ.code or ''),
                           'Discriminacao':  somente_ascii(str(ServId.name or '')),
                           'CodigoMunicipio': MyCidadeCode,
                           }

            preenche(cpServico, cpServicoNFSE)


            cpValServNFSE = {
                           'ValorServicos': converte_valor_xml(LinhaInv.price_subtotal),
                           'ValorDeducoes': '0.00',
                           'ValorPis': '0.00',
                           'ValorCofins': '0.00',
                           'ValorInss': '0.00',
                           'ValorIr': '0.00',
                           'ValorCsll': '0.00',
                           'IssRetido': '1', #1 - Tetido na Fonte / 2 - Não Retido na Fonte
                           'ValorIss': '0.00',
                           'ValorIssRetido': '0.00',
                           'OutrasRetencoes': '0.00',
                           'BaseCalculo': '0.00',
                           'ValorLiquidoNfse': converte_valor_xml(LinhaInv.price_total),
                           'DescontoIncondicionado': converte_valor_xml(LinhaInv.discount_value),
                           'DescontoCondicionado': '0.00',
                           }

            preenche(cpValServ, cpValServNFSE)

            cpPrestadNFSE = {
                           'Cnpj': limpa_cnpj_cpf(str(mypartner.cnpj_cpf or '')),
                           'InscricaoMunicipal': str(mypartner.inscr_mun or ''),
                           }

            preenche(cpPrestad, cpPrestadNFSE)

            cpTomadorNFSE = {
                           'RazaoSocial': somente_ascii(str(partner.legal_name or '')),
                           }

            preenche(cpTomador, cpTomadorNFSE)

            cpEndTomaNFSE = {
                           'Endereco': somente_ascii(str(partner.street or '')),
                           'Numero': partner.number or '',
                           'Complemento': somente_ascii(str(partner.street2 or '')),
                           'Bairro': somente_ascii(str(partner.district or '')),
                           'CodigoMunicipio': CidadeCode,
                           'Uf': partner.l10n_br_city_id.state_id.code or '',
                           'Cep': str(partner.zip or '').replace("-",""),
                           }

            preenche(cpEndToma, cpEndTomaNFSE)

            if partner.is_company:
                cpCNPTomaNFSE = {
                               'Cnpj': limpa_cnpj_cpf(str(partner.cnpj_cpf or '')),
                               }
            else:
                cpCNPTomaNFSE = {
                               'Cpf': limpa_cnpj_cpf(str(partner.cnpj_cpf or '')),
                               }

            preenche(cpCNPToma, cpCNPTomaNFSE)

            cpConTomaNFSE = {
                           'Telefone': partner.phone or '',
                           'Email': partner.email or '',
                           }

            preenche(cpConToma, cpConTomaNFSE)

            cpIdeToma.append( cpCNPToma )
            cpTomador.append( cpIdeToma )
            cpTomador.append( cpConToma )
            cpTomador.append( cpEndToma )
            cpServico.append( cpValServ )
            cpInfRps.append( cpIdentRps )
            cpInfRps.append( cpServico )
            cpInfRps.append( cpPrestad )
            cpInfRps.append( cpTomador )
            cpRps.append( cpInfRps )
            ListaRps.append( cpRps )
 
        var['NumeroLote'] = str(nrVlLote)
        var['Cnpj'] = str(mypartner.cnpj_cpf or '')
        var['InscricaoMunicipal'] = str(mypartner.inscr_mun or '') 
        var['QuantidadeRps'] = str(qtdeRPS)
        preenche(loteRps, var)
 
        recursively_empty(EnviarLote)
        
        res = {'arquivo': CABECALHO_XML + etree.tostring(EnviarLote)}
        return res
        
    def gera_rps(self, cr, uid, id, nrLote, context=None):
        if context is None:
            context = {}

        rps = self.gera_arquivo_xml(cr, uid, id, nrLote, context)
        rps['nome'] ='RPS_L'+nrLote+'_'+time.strftime('%Y%m%d_%H%M%S')+'.xml'
        rps['lote'] ='RPS_L'+nrLote
        return rps
    
    def reemite_rps(self, cr, uid, ids, context=None):
        """Confirma o Processamento do Contrato"""
        if Log:
            _logger.info("contract_confirm")
        if context is None:
            context = {}
        
        for id in ids:
            this = self.browse(cr, uid, id)
            nrLote = this.numero
            rps = self.gera_rps(cr, uid, id, nrLote, context)
            self.write(cr, uid, ids, {'data_out': time.strftime('%Y-%m-%d')}, context=context)
            self.anexarRps(cr,uid,id,rps['arquivo'],rps['nome'])
        
        return False

    def emite_rps(self, cr, uid, ids, context=None):
        """Confirma o Processamento do Contrato"""
        if Log:
            _logger.info("contract_confirm")
        if context is None:
            context = {}
        
        for id in ids:
            this = self.browse(cr, uid, id)
            if this.numero:
                nrLote = this.numero
            else:
                nrLote = self.gera_id(cr, uid, id, context)
                self.write(cr, uid, ids, {'name': 'RPS_L'+nrLote, 'numero': str(nrLote)}, context=context)
            rps = self.gera_rps(cr, uid, id, nrLote, context)
            self.write(cr, uid, ids, {'data_out': time.strftime('%Y-%m-%d')}, context=context)
            self.anexarRps(cr,uid,id,rps['arquivo'],rps['nome'])
        
        return self.write(cr, uid, ids, {'state':'done'}, context=context)

    def verifica_rps(self, cr, uid, id, context=None):
        return True

    _columns = {
                'name': fields.char('Lote', 30, readonly=True),
                'numero': fields.char(u'Número',5),
                'data_in': fields.date(u'Data da Criação',),
                'data_out': fields.date(u'Data de Geração',),
                'invoice_ids' : fields.one2many('account.invoice','loterps_id','Lote RPS', readonly=True),
                'company_id': fields.many2one('res.company', 'Empresa',),
                'state': fields.selection([
                                           ('draft', 'Novo'),
                                           ('done', 'Gerado'),
                                           ('cancel','Cancelado')
                                           ]),
                }
    
    _defaults = {
                'company_id': lambda s,cr,uid,c: s.pool.get('res.company')._company_default_get(cr, uid, 'ir.attachment', context=c),
                'data_in': lambda *a: time.strftime('%Y-%m-%d'),
                'state': 'draft',
                }

loterps()