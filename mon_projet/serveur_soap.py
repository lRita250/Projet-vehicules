# -*- coding: utf-8 -*-
"""
Created on Wed Oct 11 10:45:57 2023

@author: user
"""

from spyne import Application, rpc, ServiceBase, Double
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication

class CalculateurTempsTrajetService(ServiceBase):

    @rpc(Double, Double, Double, _returns=Double)
    def calculer_temps_trajet(ctx, distance, autonomie, temps_chargement):
        nombre_de_recharges = distance / autonomie
        return (distance / autonomie * 60) + (nombre_de_recharges * temps_chargement)

application = Application([CalculateurTempsTrajetService],
    tns='my.namespace',
    in_protocol=Soap11(validator='lxml'),
    out_protocol=Soap11()
)

wsgi_application = WsgiApplication(application)
if __name__ == '__main__':
    from wsgiref.simple_server import make_server

    server = make_server('127.0.0.1', 8000, wsgi_application)
    print("Votre service SOAP est en cours d'exécution sur http://127.0.0.1:8000/")
    server.serve_forever()
