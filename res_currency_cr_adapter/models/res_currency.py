# copyright  2018 Carlos Wong, Akurey S.A.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.addons import decimal_precision as dp
from suds.client import Client
from suds.xsd.doctor import Import, ImportDoctor
from xmlrpc.client import ServerProxy
import datetime
import xml.etree.ElementTree
import logging

_logger = logging.getLogger(__name__)


class ResCurrencyRate(models.Model):
    _inherit = 'res.currency'

    rate = fields.Float(digits=dp.get_precision('Currency Rate Precision'))


class ResCurrencyRate(models.Model):
    _inherit = 'res.currency.rate'

    # Change decimal presicion to work with CRC where 1 USD is more de 555 CRC
    rate = fields.Float(string='Selling Rate',
                        digits=dp.get_precision('Currency Rate Precision'))

    # Costa Rica uses two exchange rates:
    #   - Buying exchange rate - used when a financial institutions buy USD from you (rate)
    #   - Selling exchange rate - used when financial institutions sell USD to you (rate_2)
    rate_2 = fields.Float(string='Buying Rate', digits=dp.get_precision('Currency Rate Precision'),
                          help='The buying rate of the currency to the currency of rate 1.')

    # Rate as it is get
    original_rate = fields.Float(string='Selling Rate in Costa Rica', digits=(6, 2),
                                 help='The selling exchange rate from CRC to USD as it is send from BCCR')

    # Rate as it is get
    original_rate_2 = fields.Float(string='Buying Rate in Costa Rica', digits=(6, 2),
                                   help='The buying exchange rate from CRC to USD as it is send from BCCR')

    @api.model
    def _cron_update(self):

        _logger.debug(
            "=========================================================")
        _logger.debug("Executing exchange rate update from 1 CRC = X USD")

        company_name = self.env.user.company_id.name

        # Get current date to get exchange rate for today
        currentDate = datetime.datetime.now().date()
        # formato requerido por el BCCR dd/mm/yy
        today = currentDate.strftime('%d/%m/%Y')

        # Get XML Schema for BCCR webservice SOAP
        imp = Import('http://www.w3.org/2001/XMLSchema', location='http://www.w3.org/2001/XMLSchema.xsd')
        imp.filter.add('http://ws.sdde.bccr.fi.cr')

        # Web Service Connection using the XML schema from BCCRR
        client = Client('http://indicadoreseconomicos.bccr.fi.cr/indicadoreseconomicos/WebServices/wsIndicadoresEconomicos.asmx?WSDL',
                        doctor=ImportDoctor(imp))

        # Get Selling exchange Rate from BCCR
        # Indicators IDs at https://www.bccr.fi.cr/seccion-indicadores-economicos/servicio-web
        # The response is a string we need to convert it to XML to extract value

        response = client.service.ObtenerIndicadoresEconomicosXML(tcIndicador='318',
                                                                  tcFechaInicio=today,
                                                                  tcFechaFinal=today,
                                                                  tcNombre=company_name,
                                                                  tnSubNiveles='N')
        xmlResponse = xml.etree.ElementTree.fromstring(response)
        rateNodes = xmlResponse.findall("./INGC011_CAT_INDICADORECONOMIC/NUM_VALOR")
        sellingRate = 0
        if len(rateNodes) > 0:
            sellingOriginalRate = float(rateNodes[0].text)
            # Odoo uses the value of 1 unit of the base currency divided between the exchage rate
            sellingRate = 1 / sellingOriginalRate

        # Get Buying exchange Rate from BCCR
        response = client.service.ObtenerIndicadoresEconomicosXML(tcIndicador='317',
                                                                  tcFechaInicio=today,
                                                                  tcFechaFinal=today,
                                                                  tcNombre=company_name,
                                                                  tnSubNiveles='N')

        xmlResponse = xml.etree.ElementTree.fromstring(response)
        rateNodes = xmlResponse.findall("./INGC011_CAT_INDICADORECONOMIC/NUM_VALOR")
        buyingRate = 0
        if len(rateNodes) > 0:
            buyingOriginalRate = float(rateNodes[0].text)
            # Odoo uses the value of 1 unit of the base currency divided between the exchage rate
            buyingRate = 1 / buyingOriginalRate

        # Save the exchange rate in database
        today = currentDate.strftime('%Y-%m-%d')

        # GET THE CURRENCY ID
        currency_id = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)

        # Get the rate for this date to know it is already registered
        ratesIds = self.env['res.currency.rate'].search([('name', '=', today)], limit=1)

        if len(ratesIds) > 0:
            newRate = ratesIds.write({'rate': sellingRate,
                                      'original_rate': sellingOriginalRate,
                                      'rate_2': buyingRate,
                                      'original_rate_2': buyingOriginalRate,
                                      'currency_id': currency_id.id})
            _logger.debug({'name': today,
                           'rate': sellingRate,
                           'original_rate': sellingOriginalRate,
                           'rate_2': buyingRate,
                           'original_rate_2': buyingOriginalRate,
                           'currency_id': currency_id.id})
        else:
            newRate = self.create({'name': today,
                                   'rate': sellingRate,
                                   'original_rate': sellingOriginalRate,
                                   'rate_2': buyingRate,
                                   'original_rate_2': buyingOriginalRate,
                                   'currency_id': currency_id.id})
            _logger.debug({'name': today,
                           'rate': sellingRate,
                           'original_rate': sellingOriginalRate,
                           'rate_2': buyingRate,
                           'original_rate_2': buyingOriginalRate,
                           'currency_id': currency_id.id})

        _logger.debug(
            "=========================================================")

    @api.model
    def _cron_update_crc2usd_rate(self):

        _logger.debug("=========================================================")
        _logger.debug("Executing exchange rate update, 1 USD = X CRC")

        company_name = self.env.user.company_id.name

        # Get current date to get exchange rate for today
        currentDate = datetime.datetime.now().date()
        # formato requerido por el BCCR dd/mm/yy
        today = currentDate.strftime('%d/%m/%Y')

        # Get XML Schema for BCCR webservice SOAP
        imp = Import('http://www.w3.org/2001/XMLSchema', location='http://www.w3.org/2001/XMLSchema.xsd')
        imp.filter.add('http://ws.sdde.bccr.fi.cr')

        # Web Service Connection using the XML schema from BCCRR
        client = Client('http://indicadoreseconomicos.bccr.fi.cr/indicadoreseconomicos/WebServices/wsIndicadoresEconomicos.asmx?WSDL',
                        doctor=ImportDoctor(imp))

        # Get Selling exchange Rate from BCCR
        # Indicators IDs at https://www.bccr.fi.cr/seccion-indicadores-economicos/servicio-web
        # The response is a string we need to convert it to XML to extract value

        response = client.service.ObtenerIndicadoresEconomicosXML(tcIndicador='318',
                                                                  tcFechaInicio=today,
                                                                  tcFechaFinal=today,
                                                                  tcNombre=company_name,
                                                                  tnSubNiveles='N')
        xmlResponse = xml.etree.ElementTree.fromstring(response)
        rateNodes = xmlResponse.findall("./INGC011_CAT_INDICADORECONOMIC/NUM_VALOR")
        sellingRate = 0
        if len(rateNodes) > 0:
            sellingOriginalRate = float(rateNodes[0].text)
            sellingRate = sellingOriginalRate

        # Get Buying exchange Rate from BCCR
        response = client.service.ObtenerIndicadoresEconomicosXML(tcIndicador='317',
                                                                  tcFechaInicio=today,
                                                                  tcFechaFinal=today,
                                                                  tcNombre=company_name,
                                                                  tnSubNiveles='N')

        xmlResponse = xml.etree.ElementTree.fromstring(response)
        rateNodes = xmlResponse.findall("./INGC011_CAT_INDICADORECONOMIC/NUM_VALOR")
        buyingRate = 0
        if len(rateNodes) > 0:
            buyingOriginalRate = float(rateNodes[0].text)
            buyingRate = buyingOriginalRate

        # Save the exchange rate in database
        today = currentDate.strftime('%Y-%m-%d')

        # GET THE CURRENCY ID
        currency_id = self.env['res.currency'].search([('name', '=', 'USD')], limit=1)
        ratesIds = self.env['res.currency.rate'].search([('name', '=', today)], limit=1)

        if len(ratesIds) > 0:
            newRate = ratesIds.write({'rate': sellingRate,
                                      'original_rate': sellingOriginalRate,
                                      'rate_2': buyingRate,
                                      'original_rate_2': buyingOriginalRate,
                                      'currency_id': currency_id.id})

            _logger.debug({'name': today,
                           'rate': sellingRate,
                           'original_rate': sellingOriginalRate,
                           'rate_2': buyingRate,
                           'original_rate_2': buyingOriginalRate,
                           'currency_id': currency_id.id})
        else:
            newRate = self.create({'name': today,
                                   'rate': sellingRate,
                                   'original_rate': sellingOriginalRate,
                                   'rate_2': buyingRate,
                                   'original_rate_2': buyingOriginalRate,
                                   'currency_id': currency_id.id})

            _logger.debug({'name': today,
                           'rate': sellingRate,
                           'original_rate': sellingOriginalRate,
                           'rate_2': buyingRate,
                           'original_rate_2': buyingOriginalRate,
                           'currency_id': currency_id.id})

        _logger.debug(
            "=========================================================")
