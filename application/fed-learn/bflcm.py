# Copyright 2020 Adap GmbH. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Flower ClientManager."""

from flwr.server import SimpleClientManager, client_proxy
from flwr.common import GetPropertiesIns

class BFLClientManager(SimpleClientManager):
    """Provides a pool of available clients."""

    def get_client(self, cid: str, timeout: float = 0.0) -> client_proxy.ClientProxy:
        """Return client of id 'cid'. Can set wait to wait for the specific client to join. Otherwise return None.

        Args:
            cid (str): Client id
            timeout (float | None): Maximum time to wait for client availability, defaults to 0.
        """
        
        # If self.clients use other as key but client class has cid 

        with self._cv:
            self._cv.wait_for(
                lambda: self.__client_with_cid(cid) != None, timeout=timeout
        )
            
        return self.__client_with_cid(cid)
    
    def __client_with_cid(self, cid):
        
        # If self.clients dict use cid as key (Can be defined in start_simulation)
        if cid in self.clients.keys():
            return self.clients[cid] 

        res = [client for client in self.clients.values() if client.get_properties(GetPropertiesIns({}), 0).properties["cid"] == cid]
        return res[0] if len(res) > 0 else None

