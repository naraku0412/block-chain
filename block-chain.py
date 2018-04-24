#!/usr/local/bin/python
# -*- coding: UTF-8 -*-
import os
import hashlib
import json
from hashlib import sha256
from time import time, asctime
from uuid import uuid4
from textwrap import dedent
from uuid import uuid4
from flask import Flask, jsonify, request, render_template
from urllib.parse import urlparse
import requests
import pickle
from optparse import OptionParser
 
def parse_opts(parser):
    parser.add_option("-p","--port",action="store",type="int",dest="port",default=8080,help="the working port")
    (options,args) = parser.parse_args()

    return options

class Blockchain(object):
    def __init__(self):
        self.current_transactions = []
        self.chain = []
        # Create the genesis block
        self.new_block(previous_hash=1, proof=100)
        self.nodes = set()
    def new_block(self, proof, previous_hash=None):
        """
        生成新块
        :param proof: <int> The proof given by the Proof of Work algorithm
        :param previous_hash: (Optional) <str> Hash of previous Block
        :return: <dict> New Block
        """
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }
        # Reset the current list of transactions
        self.current_transactions = []
        self.chain.append(block)
        return block
    def new_transaction(self, sender, recipient, amount):
        """
        生成新交易信息，信息将加入到下一个待挖的区块中
        :param sender: <str> Address of the Sender
        :param recipient: <str> Address of the Recipient
        :param amount: <int> Amount
        :return: <int> The index of the Block that will hold this transaction
        """
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })
        return self.last_block['index'] + 1
    def new_transaction_v1(self, _id, src, dst):
        """
        生成新交易信息，信息将加入到下一个待挖的区块中
        :param sender: <str> Address of the Sender
        :param recipient: <str> Address of the Recipient
        :param amount: <int> Amount
        :return: <int> The index of the Block that will hold this transaction
        """
        self.current_transactions.append({
            'id': _id,
            'src': src,
            'dst': dst,
        })
        return self.last_block['index'] + 1
    def new_checkpoint(self, _id, _temp, _status,_date):
        """
        generate a new checkpoint info, to be written to the coming block 
        :param id: <str> ID of the item
        :param tmp: <iint> Temperature
        :param status: <str> Status info
        :return: <int> The index of the Block that will hold this info 
        """
        self.current_transactions.append({
            'id': _id,
            'temp': _temp,
            'status': _status,
            'date': _date,
        })
        return self.last_block['index'] + 1
    @property
    def last_block(self):
        return self.chain[-1]
    @staticmethod
    def hash(block):
        """
        生成块的 SHA-256 hash值
        :param block: <dict> Block
        :return: <str>
        """
        # We must make sure that the Dictionary is Ordered, or we'll have inconsistent hashes
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()
    def proof_of_work(self, last_proof):
        """
        简单的工作量证明:
         - 查找一个 p' 使得 hash(pp') 以4个0开头
         - p 是上一个块的证明,  p' 是当前的证明
        :param last_proof: <int>
        :return: <int>
        """
        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1
        return proof
    @staticmethod
    def valid_proof(last_proof, proof):
        """
        验证证明: 是否hash(last_proof, proof)以4个0开头?
        :param last_proof: <int> Previous Proof
        :param proof: <int> Current Proof
        :return: <bool> True if correct, False if not.
        """
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == "0000"
    def register_node(self, address):
        """
        Add a new node to the list of nodes
        :param address: <str> Address of node. Eg. 'http://192.168.0.5:5000'
        :return: None
        """
        parsed_url = urlparse(address)
        self.nodes.add(parsed_url.netloc)
    def valid_chain(self, chain):
        """
        Determine if a given blockchain is valid
        :param chain: <list> A blockchain
        :return: <bool> True if valid, False if not
        """
        last_block = chain[0]
        current_index = 1
        while current_index < len(chain):
            block = chain[current_index]
            print(f'{last_block}')
            print(f'{block}')
            print("\n-----------\n")
            # Check that the hash of the block is correct
            if block['previous_hash'] != self.hash(last_block):
                return False
            # Check that the Proof of Work is correct
            if not self.valid_proof(last_block['proof'], block['proof']):
                return False
            last_block = block
            current_index += 1
        return True
    def resolve_conflicts(self):
        """
        共识算法解决冲突
        使用网络中最长的链.
        :return: <bool> True 如果链被取代, 否则为False
        """
        neighbours = self.nodes
        new_chain = None
        # We're only looking for chains longer than ours
        max_length = len(self.chain)
        # Grab and verify the chains from all the nodes in our network
        for node in neighbours:
            print(node)
            response = requests.get(f'http://{node}/chain')
            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                # Check if the length is longer and the chain is valid
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain
        # Replace our chain if we discovered a new, valid chain longer than ours
        if new_chain:
            self.chain = new_chain
            return True
        return False

options = parse_opts(OptionParser(usage="%prog [options]"))
# Instantiate our Node
app = Flask(__name__)
app.secret_key = os.urandom(24) 
# Generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')
# Instantiate the Blockchain
fn = os.path.join("/mnt","block-chain.pkl") 
if os.path.exists(fn):
    with open(fn,'rb') as f:
        blockchain = pickle.load(f)
else:
    blockchain = Blockchain()
@app.route('/', methods=['GET'])
@app.route('/index', methods=['GET'])
def index():
    return render_template('index.html')
@app.route('/healthz', methods=['GET'])
def healthz():
    response = {
        'status': "normal",
        'time': str(asctime()),
    }
    return jsonify(response), 200
@app.route('/mine', methods=['GET'])
def mine():
    # We run the proof of work algorithm to get the next proof...
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)
    # 给工作量证明的节点提供奖励.
    # 发送者为 "0" 表明是新挖出的币
    blockchain.new_transaction(
        sender="0",
        recipient=node_identifier,
        amount=1,
    )
    # Forge the new Block by adding it to the chain
    block = blockchain.new_block(proof)
    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    with open(fn,'wb') as f:
        pickle.dump(blockchain,f)
    return jsonify(response), 200
def mine_v1():
    # We run the proof of work algorithm to get the next proof...
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)
    # 给工作量证明的节点提供奖励.
    # 发送者为 "0" 表明是新挖出的币
    blockchain.new_transaction(
        sender="0",
        recipient=node_identifier,
        amount=1,
    )
    # Forge the new Block by adding it to the chain
    block = blockchain.new_block(proof)
    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    with open(fn,'wb') as f:
        pickle.dump(blockchain,f)
    return response
@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.get_json()
    # Check that the required fields are in the POST'ed data
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400
    # Create a new Transaction
    index = blockchain.new_transaction(values['sender'], values['recipient'], values['amount'])
    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201
@app.route('/checkpoints/new', methods=['POST'])
def new_checkpoint():
    values = request.get_json()
    # Check that the required fields are in the POST'ed data
    required = ['id', 'temp', 'status','date']
    if not all(k in values for k in required):
        return 'Missing values', 400
    # Create a new Checkpoint 
    index = blockchain.new_checkpoint(values['id'], values['temp'], values['status'],values['date'])
    response = {'message': f'Checkpoint will be added to Block {index}'}
    return jsonify(response), 201
@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200
@app.route('/chain_ret', methods=['GET'])
def chain_ret(chain=None):
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return render_template('chain.html', chain=response) 
@app.route('/nodes/register', methods=['POST'])
def register_nodes():
    values = request.get_json()
    nodes = values.get('nodes')
    if nodes is None:
        return "Error: Please supply a valid list of nodes", 400
    for node in nodes:
        blockchain.register_node(node)
    response = {
        'message': 'New nodes have been added',
        'total_nodes': list(blockchain.nodes),
    }
    return jsonify(response), 201
@app.route('/nodes/resolve', methods=['GET'])
def consensus():
    replaced = blockchain.resolve_conflicts()
    if replaced:
        response = {
            'message': 'Our chain was replaced',
            'new_chain': blockchain.chain
        }
    else:
        response = {
            'message': 'Our chain is authoritative',
            'chain': blockchain.chain
        }
    return jsonify(response), 200
@app.route('/ret/')
def ret(msg=None):
    return render_template('ret.html', msg=msg)
@app.route('/hello/')
@app.route('/hello/<name>')
def hello(name=None):
    return render_template('hello.html', name=name)
@app.route('/test')
def test(name=None):
    return render_template('test.html')
@app.route('/typing', methods=['GET','POST'])
def typing():
    return render_template('typing.html')
@app.route('/searching', methods=['GET','POST'])
def searching():
    return render_template('searching.html')
@app.route('/checkpoint_type', methods=['GET','POST'])
def checkpoint_type():
    values = request.form
    # Check that the required fields are in the POST'ed data
    required = ['id','temp','status','date']
    if not all(k in values for k in required):
        return 'Missing values', 400
    # Create a new Transaction
    index = blockchain.new_checkpoint(values.get('id'), values.get('temp'), values.get('status'),values.get("date"))
    response = mine_v1()
    return render_template('ret.html',msg=response)
@app.route('/transaction_type', methods=['GET','POST'])
def transaction_type():
    values = request.form
    # Check that the required fields are in the POST'ed data
    required = ['id', 'src', 'dst']
    if not all(k in values for k in required):
        return 'Missing values', 400
    # Create a new Transaction
    index = blockchain.new_transaction_v1(values.get('id'), values.get('src'), values.get('dst'))
    response = mine_v1() 
    return render_template('ret.html',msg=response)
@app.route('/checkpoint_ret', methods=['GET','POST'])
def checkpoint_ret():
    values = request.form
    required = ['id']
    if not all(k in values for k in required):
        return 'Missing values', 400
    response = do_search(values.get("id"),marker='temp')
    return render_template('ret_v3.html',msgs=response,id=values.get("id"))
@app.route('/transaction_ret', methods=['GET','POST'])
def transaction_ret():
    values = request.form
    required = ['id']
    if not all(k in values for k in required):
        return 'Missing values', 400
    response = do_search(values.get("id"),marker='src')
    return render_template('ret_v2.html',msgs=response,id=values.get("id"))
def do_search(id0,marker):
    ret = []
    chain = blockchain.chain
    for item in chain:
        for trans in item["transactions"]:
            if marker in trans:
                if id0 == trans["id"]:
                    ret.append(trans)
    return ret
        
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=options.port)
