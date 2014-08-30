#Machine Repair Simulation
#Grissess, 2014

import sys
import random

SHUFFLE_TIMES=False #Set to true to shuffle the repair and machine times per-object
#Simulation requirements MAY require this to be set to False, as it is.

STANDARD_OUTPUT=True #Output only what the standard requires us to.
#Setting this to True will output debugging information, such as the event stream.

def debug(msg, *args):
	if not STANDARD_OUTPUT:
		print 'DEBUG: ', (msg%args if args else msg)

def main():
	print 'Utilizations:'
	print 'Case|Machines|Repairman Utility|Average Computer Utility'
	fl=FileLoader(sys.stdin)
	for case, sim in fl.MakeSims():
		sim.Run()
		if not STANDARD_OUTPUT:
			print 'Event stream:'
			for ev in sim.events:
				print repr(ev)
		uc=UtilizationCalculator(sim.events)
		ru=uc.CalcNorm(sim.GetRepairMan(), RepairMan.STATE_REPAIRING)
		mus=[]
		for m in sim.machines:
			mus.append(uc.CalcNorm(m, Machine.STATE_RUNNING))
		if not STANDARD_OUTPUT:
			print 'Per-machine utilities:'
			for idx, mu in enumerate(mus):
				print '%d: %.3f'%(idx, mu)
		mua=sum(mus)/len(mus)
		print '%4d|%8d|%17.3f|%.3f'%(case, len(mus), ru, mua)
	print 'End of program.'

class FileLoader(object):
	def __init__(self, f):
		self.f=f
	def SkipLine(self):
		self.f.readline()
	def ReadList(self):
		return map(float, filter(None, self.f.readline().split(' ')))
		#Alternatively: return [float(i) for i in self.f.readline().split(' ') if i]
	def MakeSims(self):
		self.SkipLine()
		runtimes=self.ReadList()
		self.SkipLine()
		reptimes=self.ReadList()
		self.SkipLine()
		simparams=self.ReadList()
		case=1
		while simparams and simparams != [0.0, 0.0]:
			debug('Starting case %d with params %r', case, simparams)
			sim=Simulator([], [], simparams[0])
			if SHUFFLE_TIMES:
				random.shuffle(reptimes)
			sim.AddRepairMan(RepairMan(sim, reptimes)) #XXX Circular dependency, also only one ever allowed though multiple are supported
			for i in xrange(int(simparams[1])):
				if SHUFFLE_TIMES:
					random.shuffle(runtimes)
				sim.AddMachine(Machine(sim, runtimes))
			yield case, sim #Simulator, runtime
			case+=1
			simparams=self.ReadList()

class CyclicQueue(object):
	def __init__(self, queue):
		self.queue=list(queue)
		self.idx=0
	def Pull(self):
		ret=self.queue[self.idx]
		self.idx+=1
		if self.idx>=len(self.queue):
			self.idx=0
		return ret
	def Peek(self):
		return self.queue[self.idx]
	def Add(self, obj):
		self.queue.append(obj)
	def __getitem__(self, item):
		return self.queue[item]
	def __len__(self):
		return len(self.queue)
	
class UtilizationCalculator(object):
	def __init__(self, evstream):
		self.evstream=evstream
		self.inittime=list(self.SearchEvents(StartEvent))[-1].time
		self.finaltime=list(self.SearchEvents(StopEvent))[-1].time
		debug('Calculated init/final sim times: %f - %f', self.inittime, self.finaltime)
	def SearchEvents(self, tp, filter=None):
		for i in self.evstream:
			if isinstance(i, tp) and (filter is None or filter(i)):
				yield i
	@staticmethod
	def EvFilterObject(obj):
		return lambda ev, obj=obj: isinstance(ev, StateChangeEvent) and ev.obj is obj
	def Calc(self, obj, state):
		total=0.0
		isset=False #XXX This assumption mandated the FlushStateEvent() interface
		lasttime=self.inittime
		for ev in self.SearchEvents(StateChangeEvent, self.EvFilterObject(obj)):
			debug('CALC: @%f (flag is %s) delta is %f, total is %f', ev.time, 'set' if isset else 'not set', ev.time-lasttime, total)
			if isset:
				total+=ev.time-lasttime
			lasttime=ev.time
			debug('CALC: event %r is to new state %d, desired %d', ev, ev.newstate, state)
			if ev.newstate==state:
				debug('CALC: Setting flag @%f', ev.time)
				isset=True
			else:
				debug('CALC: Clearing flag @%f', ev.time)
				isset=False
		debug('Total utility of %r: %f', obj, total)
		return total
	def SimLength(self):
		return self.finaltime-self.inittime
	def CalcNorm(self, obj, state):
		return self.Calc(obj, state)/self.SimLength()

class Simulator(object):
	def __init__(self, repairmen, machines, until, time=0.0):
		assert until>time
		self.repairmen=CyclicQueue(repairmen)
		self.machines=CyclicQueue(machines) #XXX Necessary to wrap this?
		self.until=until
		self.time=time
		self.events=[]
	def AddMachine(self, mach):
		self.machines.Add(mach)
	def AddRepairMan(self, repairman):
		self.repairmen.Add(repairman)
	def GetRepairMan(self):
		return self.repairmen.Pull()
	def AddEvent(self, ev):
		assert isinstance(ev, Event)
		self.events.append(ev)
	def Objects(self):
		for i in self.machines:
			yield i
		for i in self.repairmen:
			yield i
	def Tick(self):
		evtimes=[(obj, obj.NextEvent()) for obj in self.Objects() if obj.NextEvent() is not None] #XXX Double call
		assert evtimes
		for obj, evtime in evtimes: #XXX Should switch on debug, can't remember the var
			assert evtime>=self.time
		evtimes.sort(key=lambda x: x[1])
		obj, time=evtimes[0]
		self.time=time
		self.AddEvent(TickEvent(self.time))
		debug('Tick at %f', self.time)
		obj.DoEvent()
	def Run(self):
		self.AddEvent(StartEvent(self.time))
		debug('Simulation begins at %f', self.time)
		for obj in self.Objects():
			obj.FlushStateEvent()
		while self.time<=self.until:
			self.Tick()
		for obj in self.Objects():
			obj.FlushStateEvent()
		self.AddEvent(StopEvent(self.time))
		debug('Simulation ends at %f', self.time)
		
class Event(object):
	def __init__(self, time):
		self.time=time
	def __repr__(self):
		return '<Event @%f>'%(self.time)
	
#XXX Boilerplate
	
class TickEvent(Event):
	def __init__(self, time):
		super(TickEvent, self).__init__(time)
	def __repr__(self):
		return '<Tick @%f>'%(self.time)
	
class StartEvent(Event):
	def __init__(self, time):
		super(StartEvent, self).__init__(time)
	def __repr__(self):
		return '<Simulation start @%f>'%(self.time)
	
class StopEvent(Event):
	def __init__(self, time):
		super(StopEvent, self).__init__(time)
	def __repr__(self):
		return '<Simulation stop @%f>'%(self.time)
	
class MessageEvent(Event):
	def __init__(self, time, message):
		super(MessageEvent, self).__init__(time)
		self.message=message
	def __repr__(self):
		return '<%s @%f>'%(self.message, self.time)
	
class StateChangeEvent(Event):
	def __init__(self, time, obj, oldstate, newstate):
		super(StateChangeEvent, self).__init__(time)
		self.obj=obj
		self.oldstate=oldstate
		self.newstate=newstate
	def __repr__(self):
		return '<StateChange of %r %r->%r @%f>'%(self.obj, self.oldstate, self.newstate, self.time)
	
class SimObject(object):
	def __init__(self, sim):
		self.sim=sim
	def NextEvent(self):
		raise NotImplementedError('SimObject derivative must implement .NextEvent()')
	def DoEvent(self):
		raise NotImplementedError('SimObject derivative must implement .DoEvent()')
	def FlushStateEvent(self):
		raise NotImplementedError('SimObject derivative must implement .FlushStateEvent()')
		
class RepairMan(SimObject):
	STATE_IDLE=0
	STATE_REPAIRING=1
	def __init__(self, sim, repairtimes, state=STATE_IDLE):
		super(RepairMan, self).__init__(sim)
		self.repairtimes=CyclicQueue(repairtimes)
		self.state=state
		self.queue=[]
		self.machine=None
	def __repr__(self):
		return '<RepairMan state=%d>'%(self.state)
	def NextEvent(self):
		if not self.machine:
			return None
		return self.nextevent
	def DoEvent(self):
		assert self.machine and self.state==self.STATE_REPAIRING
		self.machine.FinishRepair()
		if self.queue:
			self.machine=self.queue.pop(0)
			debug('Repairing %r', self.machine)
			self.machine.BeginRepair(self)
			self.ResetTimes()
			debug('...repair will finish at %f', self.nextevent)
		else:
			self.sim.AddEvent(StateChangeEvent(self.sim.time, self, self.state, self.STATE_IDLE))
			self.state=self.STATE_IDLE
			debug('Finished repairs')
			self.machine=None
	def ResetTimes(self):
		self.lastevent=self.sim.time
		self.nextevent=self.sim.time+self.repairtimes.Pull()
	def Request(self, machine):
		self.queue.append(machine)
		if not self.machine:
			assert self.state==self.STATE_IDLE
			self.sim.AddEvent(StateChangeEvent(self.sim.time, self, self.state, self.STATE_REPAIRING))
			self.state=self.STATE_REPAIRING
			self.machine=self.queue.pop(0)
			debug('Repairing %r', self.machine)
			self.machine.BeginRepair(self)
			self.ResetTimes()
			debug('...repair will finish at %f', self.nextevent)
	def FlushStateEvent(self):
		self.sim.AddEvent(StateChangeEvent(self.sim.time, self, None, self.state))

class Machine(SimObject):
	STATE_RUNNING=0
	STATE_WAITING=1
	STATE_REPAIRING=2
	def __init__(self, sim, runtimes, state=STATE_RUNNING):
		super(Machine, self).__init__(sim)
		self.runtimes=CyclicQueue(runtimes)
		self.state=state
		self.ResetTimes()
	def __repr__(self):
		return '<Machine state=%d>'%(self.state)
	def NextEvent(self):
		if self.state==self.STATE_RUNNING:
			return self.nextevent
		return None #XXX superfluous
	def ResetTimes(self):
		self.lastevent=self.sim.time
		self.nextevent=self.sim.time+self.runtimes.Pull()
	def DoEvent(self):
		self.BreakDown()
	def BreakDown(self):
		debug('Breaking down from state %d', self.state)
		assert self.state==self.STATE_RUNNING
		self.sim.AddEvent(StateChangeEvent(self.sim.time, self, self.state, self.STATE_WAITING))
		self.state=self.STATE_WAITING
		self.sim.GetRepairMan().Request(self)
	def BeginRepair(self, repairman):
		debug('Repairing from state %d', self.state)
		assert self.state==self.STATE_WAITING
		self.sim.AddEvent(StateChangeEvent(self.sim.time, self, self.state, self.STATE_REPAIRING))
		self.state=self.STATE_REPAIRING
	def FinishRepair(self):
		debug('Starting from state %d', self.state)
		assert self.state==self.STATE_REPAIRING
		self.sim.AddEvent(StateChangeEvent(self.sim.time, self, self.state, self.STATE_RUNNING))
		self.state=self.STATE_RUNNING
		self.ResetTimes()
		debug('...machine will break down at %f', self.nextevent)
	def FlushStateEvent(self):
		self.sim.AddEvent(StateChangeEvent(self.sim.time, self, None, self.state))
		
if __name__=='__main__':
	main()