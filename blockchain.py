import logging


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class BlockChain:
    def __init__(self, chain):
        self.chain = chain


    def is_chain_valid(self, chain):
        if not chain:
            logging.error("Chain is empty or null.")
            return False
    
        if not chain[0].is_valid_hash() or chain[0].prev_hash != '0' * 64:
            logging.error("Block 1: Invalid hash or invalid prev_hash")
            return False
        
        for i in range(1, len(chain)):
            current_block = chain[i]
            previous_block = chain[i - 1]
            if current_block.prev_hash != previous_block.curr_hash:
                logging.error(f"Block {current_block.block_number}: Invalid previous hash.")
                return False
            if current_block.curr_hash != current_block.calculate_hash():
                logging.error(f"Block {current_block.block_number}: Hash does not match stored value.")
                return False
        return True
    

    def add_block(self, block):
        if len(self.chain) == 0 or block.prev_hash == self.chain[-1].curr_hash:
            self.chain.append(block)
        else:
            logging.error("Block rejected due to invalid previous hash.")