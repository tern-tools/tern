from abc import abstractmethod
from abc import ABCMeta

class Template(object):
     __metaclass__ == ABCMeta
     

     @abstractmethod
     def package():
         pass
     
     @abstractmethod
     def layer():
         pass
     
     @abstractmethod
     def image():
         pass
     
     @abstractmethod
     def notice():
         pass
     
     @abstractmethod
     def notice_origin():
         pass
     
     @abstractmethod
     def origins():
         pass
