import requests
import hashlib
import hmac
import csv
import base64
import json
import csv 
from collections import defaultdict
import copy

def hash_key(message):
    a = str.encode(message, encoding="utf-8")
    hash = hmac.new(b'eRlUTImwkJqba#E', a, hashlib.sha1).digest()
    b = base64.encodestring(hash)
    b = b.rstrip()
    return "INTEGRACION grupo3:" + b.decode("utf-8")

def get_almacenes():
    uri = 'https://integracion-2019-prod.herokuapp.com/bodega/'
    headers={"Content-Type": "application/json", "Authorization": hash_key('GET')}
    r = requests.get(uri+'almacenes', headers=headers)
    return r.json()

def skusWithStock(x):
    almacenes = {
                'recepcion': '5cc7b139a823b10004d8e6d9',
                'pulmon': '5cc7b139a823b10004d8e6dd',
                'cocina': '5cc7b139a823b10004d8e6de',
                'despacho': '5cc7b139a823b10004d8e6da',
                'otro1': "5cc7b139a823b10004d8e6dc",
                'otro2': "5cc7b139a823b10004d8e6db"
            }
    uri = 'https://integracion-2019-prod.herokuapp.com/bodega/'
    headers={"Content-Type": "application/json", "Authorization": str(hash_key('GET'+almacenes[x]))}
    r = requests.get(uri+'skusWithStock', headers=headers, params={"almacenId":almacenes[x]})
    return r.json()

def ver_stock():
    stock = defaultdict(lambda: 0) 
    for a in ['despacho', 'recepcion', 'cocina', 'pulmon', 'otro1', 'otro2']:
        for i in skusWithStock(a):
            stock[i['_id']] += i['total']
    return stock

def minimos():
    dict_minimos = {}
    with open('Minimos.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                line_count += 1
            else:
                dict_minimos[row[0]] = {"nombre": row[1], "cantidad": row[3]}
                line_count += 1
    return dict_minimos

def dict_ingredientes():
    dict_ingredientes = defaultdict(list)
    with open('Ingredientes.csv') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=',')
        line_count = 0
        for row in csv_reader:
            if line_count == 0:
                line_count += 1
            else:
                dict_ingredientes[row[0]].append({"sku_ingrediente": row[2], "lote": int(float(row[6])),  "cantidad": int(float(row[9]))})
                line_count += 1
    return dict_ingredientes

# FabricarSinPago
def Fabricar(sku, cantidad):
    uri = 'https://integracion-2019-prod.herokuapp.com/bodega/'
    headers={"Content-Type": "application/json", "Authorization": str(hash_key(str('PUT'+sku+str(cantidad))))}
    enviar = requests.put(uri+'fabrica/fabricarSinPago', headers=headers, json={"sku":sku, 'cantidad':cantidad})
    return enviar.json()

def cual_falta(prod, cantidad, lote):
    ing = dict_ingredientes()
    necesitan = []
    actuales = copy.deepcopy(ing[prod])
    for i in actuales:
        cantidad_necesaria = (int(cantidad / (lote)) +1) * i['cantidad']
        i['cantidad_necesaria'] = cantidad_necesaria
    materias_primas = defaultdict(lambda: 0)
    while len(actuales) > 0:
        actual = actuales.pop()
        ing_actuales = ing[actual['sku_ingrediente']]
        if len(ing_actuales) > 0:
            for i in ing_actuales:
                cantidad_necesaria = (int(actual['cantidad_necesaria'] / (i['lote'])) +1) * i['cantidad']
                i['cantidad_necesaria'] = cantidad_necesaria
                actuales.append(i)
        else:
            materias_primas[actual['sku_ingrediente']] += actual['cantidad_necesaria']
    return materias_primas

def cual_falta_total():
    mini = minimos()
    ings = dict_ingredientes()
    stock = ver_stock()
    faltan = defaultdict(lambda: 0)
    for i in mini:
        if i in stock and stock[i] > int(mini[i]['cantidad']):
            print('Ya hay suficiente')
            print(i)
        else:
            if i in stock:
                mini[i]['cantidad'] = str(int(mini[i]['cantidad'])- stock[i])
            if len(ings[i])> 0:
                necesario_x = cual_falta(i, int(mini[i]['cantidad']), int(int(ings[i][0]['lote'])))
                for x in necesario_x:
                    faltan[x] += necesario_x[x]
            else:
                faltan[i] += int(mini[i]['cantidad'])
    #comparar con stock
    for x in stock:
        if x in faltan:
            if faltan[x] < stock[x]:
                faltan.pop(x)
    return faltan

def esta_completo(sku, cantidad, lote):
    almacenes = {
                'recepcion': '5cc7b139a823b10004d8e6d9',
                'pulmon': '5cc7b139a823b10004d8e6dd',
                'cocina': '5cc7b139a823b10004d8e6de',
                'despacho': '5cc7b139a823b10004d8e6da',
                'otro1': "5cc7b139a823b10004d8e6dc",
                'otro2': "5cc7b139a823b10004d8e6db"
            }
    todos = True
    f = cual_falta(sku, cantidad, lote)
    s = ver_stock()
    for x in f:
        if x not in s:
            todos = False
    return todos

# Ver cuales de los productos minimos esta tienen todos sus ingredientes
def ver_completos():
    mini = minimos()
    ings = dict_ingredientes()
    completos = []
    for i in mini:
        if len(ings[i])> 0:
            if esta_completo(i, int(mini[i]['cantidad']), int(ings[i][0]['lote'])):
                completos.append(i)
        else:
            print('FALTA')
            print(i)
    return completos

def limpiar_despacho(origen, destino):
    almacenes = {
                'recepcion': '5cc7b139a823b10004d8e6d9',
                'pulmon': '5cc7b139a823b10004d8e6dd',
                'cocina': '5cc7b139a823b10004d8e6de',
                'despacho': '5cc7b139a823b10004d8e6da',
                'otro1': "5cc7b139a823b10004d8e6dc",
                'otro2': "5cc7b139a823b10004d8e6db"
            }
    uri = 'https://integracion-2019-prod.herokuapp.com/bodega/'
    headers={"Content-Type": "application/json", "Authorization": str(hash_key('GET'+almacenes[origen]))}
    r = requests.get(uri+'skusWithStock', headers=headers, params={"almacenId":almacenes[origen]})
    for i in r.json():
        headers={"Content-Type": "application/json", "Authorization": str(hash_key('GET'+almacenes[origen]+str(i['_id'])))}
        r2 = requests.get(uri+'stock', headers=headers, params={"almacenId":almacenes[origen], 'sku':i['_id']})
        for x in r2.json():
            headers={"Content-Type": "application/json", "Authorization": str(hash_key(str('POST'+x['_id']+almacenes[destino])))}
            enviar = requests.post(uri+'moveStock', headers=headers, json={"productoId":x['_id'], 'almacenId':almacenes[destino]})
            print(enviar.json())


def fabricar_sku(sku, falta, lote):
    almacenes = {
                'recepcion': '5cc7b139a823b10004d8e6d9',
                'pulmon': '5cc7b139a823b10004d8e6dd',
                'cocina': '5cc7b139a823b10004d8e6de',
                'despacho': '5cc7b139a823b10004d8e6da',
                'otro1': "5cc7b139a823b10004d8e6dc",
                'otro2': "5cc7b139a823b10004d8e6db"
            }
    completo = sku
    s = ver_stock()
    print(completo)
    i = dict_ingredientes()
    ings = i[completo]
    todos = True
    for i in ings:
        if i['sku_ingrediente'] not in s:
            print(i)
            todos = False
    if todos:
        print('todos')
        for i in ings:
            mover = (int(falta/lote)) * i['cantidad'] + 1
            print(mover)
            for a in almacenes:
                uri = 'https://integracion-2019-prod.herokuapp.com/bodega/'
                headers={"Content-Type": "application/json", "Authorization": str(hash_key('GET'+almacenes[a]+i['sku_ingrediente']))}
                r = requests.get(uri+'stock', headers=headers, params={"almacenId":almacenes[a], 'sku':i['sku_ingrediente']})
                for x in r.json():
                    headers={"Content-Type": "application/json", "Authorization": str(hash_key(str('POST'+x['_id']+almacenes['despacho'])))}
                    if mover > 0:
                        enviar = requests.post(uri+'moveStock', headers=headers, json={"productoId":x['_id'], 'almacenId':almacenes['despacho']})
                        print(enviar.json())
                        mover -= 1
        falta_lotes = (int(falta/lote) + 1 ) * lote
        orden = Fabricar(completo, falta_lotes)
        print(orden)
        orden['sku_destino'] = completo
        ordenes = {}
        ordenes[orden['sku']] = orden

# Imprimir el stock por almacen
def imprimir_stock_almacen():
    almacenes = {
        'recepcion': '5cc7b139a823b10004d8e6d9',
        'pulmon': '5cc7b139a823b10004d8e6dd',
        'cocina': '5cc7b139a823b10004d8e6de',
        'despacho': '5cc7b139a823b10004d8e6da', 
        'otro1': "5cc7b139a823b10004d8e6da",
        'otro2': "5cc7b139a823b10004d8e6db"
   }
    for x in almacenes:
        print(x)
        print(skusWithStock(x))

# Ver cuales elementos tienen el stock minimo
def imprimir_estado():
    m = minimos()
    s = ver_stock()
    for i in m:
        print(str(i), s[i], int(m[i]['cantidad']), s[i] >= int(m[i]['cantidad']))

# Enviar productos a otro grupo
def enviar_produtos(sku, almacenId, cantidad):
    almacenes = {
            'recepcion': '5cc7b139a823b10004d8e6d9',
            'pulmon': '5cc7b139a823b10004d8e6dd',
            'cocina': '5cc7b139a823b10004d8e6de',
            'despacho': '5cc7b139a823b10004d8e6da', 
            'otro1': "5cc7b139a823b10004d8e6da",
            'otro2': "5cc7b139a823b10004d8e6db"
    }
    for a in almacenes:
        uri = 'https://integracion-2019-prod.herokuapp.com/bodega/'
        headers={"Content-Type": "application/json", "Authorization": str(hash_key('GET'+almacenes[a]+sku))}
        r = requests.get(uri+'stock', headers=headers, params={"almacenId":almacenes[a], 'sku':sku})
        for x in r.json():
            headers={"Content-Type": "application/json", "Authorization": str(hash_key(str('POST'+x['_id']+almacenes['despacho'])))}
            if cantidad > 0:
                enviar = requests.post(uri+'moveStock', headers=headers, json={"productoId":x['_id'], 'almacenId':almacenes['despacho']})
                print(enviar.json())
                cantidad -= 1
                uri = 'https://integracion-2019-prod.herokuapp.com/bodega/'
                headers={"Content-Type": "application/json", "Authorization": str(hash_key(str('POST'+x['_id']+almacenId)))}
                enviar = requests.post(uri+'moveStockBodega', headers=headers, json={"productoId":x['_id'], 'almacenId':almacenId, 'precio': 1})
                print(enviar.json())


