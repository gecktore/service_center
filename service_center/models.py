from dataclasses import dataclass, field
from uuid import uuid4, UUID
from abc import ABC, abstractclassmethod

@dataclass
class Master:
    uid: UUID
    name: str
    phone_number: str
    grade: str = field(default="Стажер")
    accurancy: int = field(default=0) # начисления
    def to_dict(self):
        return {"uuid": str(self.uid), "name": self.name, "phone_number": self.phone_number, "grade": self.grade, "accurancy": self.accurancy}

class Application(ABC):
    uid: UUID
    device: str    
    executor: Master
    checker: Master
    dependence: Application
    type_of_work: str
    urgency: int = field(default=3) # срочность
    status: str = field(default="принята")
    numbers_of_returns: int = field(default=0)

    # def to_dict(self):
    #     return dir(self.uid)
        # return {key: value for key, value in self.__dict__.items()}
  
@dataclass
class PaidRepairAp(Application):pass
@dataclass
class WarrantyRepairAp(Application):...
@dataclass
class DiagnosticsAp(Application):...


ms1 = Master(uuid4(), "bebra1", "892893223")
ms2 = Master(uuid4(), "bebra2", "892893223")   
ms3 = Master(uuid4(), "bebra3", "892893223")   
ms4 = Master(uuid4(), "bebra4", "892893223")   
ms5 = Master(uuid4(), "bebra5", "892893223")
masters = [ms1, ms2, ms3, ms4, ms5]

# ap1 = DiagnosticsAp(uuid4(), "Ноутбук Lenovo", ms1, ms2, None)
# ap6 = PaidRepairAp(uuid4(), "Ноутбук Lenovo", ms1, ms2, ap1)
# ap2 = WarrantyRepairAp(uuid4(), "Планшет Asus", ms2, ms3, None)
# ap3 = DiagnosticsAp(uuid4(), "Компьютер Андрея", ms3, ms4, None)
# ap4 = PaidRepairAp(uuid4(), "Мышь Антона", ms4, ms5, None)
# ap5 = WarrantyRepairAp(uuid4(), "Телефон Huaway", ms5, ms1, None)
# applications = [ap1, ap2, ap3, ap4, ap5, ap6]
