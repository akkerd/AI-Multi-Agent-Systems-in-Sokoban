class Array
	def rand
		self[(Kernel.rand*length).floor]
	end
end

ACTIONS    = %w{Push Pull}
DIRECTIONS = %w{N E S W}

def rand_action1
	action    = %w{Move}.rand
	direction = DIRECTIONS.rand
	"%s(%s)" % [action, direction]
end
def rand_action2
	action    = ACTIONS.rand
	direction1 = DIRECTIONS.rand
	direction2 = DIRECTIONS.rand
	"%s(%s,%s)" % [action, direction1, direction2]
end

if ARGV.length == 1 then
	agents = ARGV[0].to_i
	while true do
		$stdin.readline
		i = 0
		s = "["
		while i < agents-1 do
			if ( rand(2) == 0 ) then
				s += rand_action1 + ","
			else
				s += rand_action2 + ","
			end
			i = i + 1
		end
			if ( rand(2) == 0 ) then
				s += rand_action1 + "]"
			else
				s += rand_action2 + "]"
			end
		puts s
		$stdout.flush
		#sleep(0.1)
	end
else
	puts "Type in number of agent"
end


