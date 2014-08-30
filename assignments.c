#define NDEBUG

#include <stdio.h>
#include <assert.h>
#include <stdlib.h>

struct ship_t {
	unsigned int top_speed;
	unsigned int fuel;
	unsigned int economy;
};

struct case_t {
	unsigned int distance;
	unsigned int successful;
	unsigned int shipsz;
	struct ship_t *ships;
};

struct sim_t {
	unsigned int casesz;
	struct case_t *cases;
};

int main(int argc, char **argv) {
	struct sim_t sim;
	struct case_t *case_;
	struct ship_t *ship;
	unsigned int caseidx;
	unsigned int shipidx;
	
	scanf("%d", &sim.casesz);
	assert(sim.casesz >= 1 && sim.casesz <= 50);
	sim.cases = (struct case_t *) malloc(sizeof(struct case_t) * sim.casesz);;
	assert(sim.cases);
	
	for(caseidx = 0; caseidx < sim.casesz; caseidx++) {
		case_ = (sim.cases + caseidx);
		case_->successful = 0;
		scanf("%d %d", &case_->shipsz, &case_->distance);
		assert(case_->shipsz >=1 && case_->shipsz <= 100);
		assert(case_->distance >=1 && case_->distance <= 1000000);
		case_->ships = (struct ship_t *) malloc(sizeof(struct ship_t) * case_->shipsz);
		assert(case_->ships);
		
		for(shipidx = 0; shipidx < case_->shipsz; shipidx++) {
			ship = (case_->ships + shipidx);
			scanf("%d %d %d", &ship->top_speed,
					&ship->fuel,
					&ship->economy);
			assert(ship->top_speed >= 1 && ship->top_speed <=1000);
			assert(ship->fuel >= 1 && ship->fuel <= 1000);
			assert(ship->economy >= 1 && ship->economy <= 1000);
			/*
			printf("Case %d Distance %d Ship %d: Fuel %d Economy %d Speed %d\n", caseidx, case_->distance, shipidx, ship->fuel, ship->economy, ship->top_speed);
			printf("...Time to Travel: %d\n", (case_->distance / ship->top_speed));
			printf("...Calculated units of fuel consumed: %d\n", (case_->distance * ship->economy) / ship->top_speed);
			*/
			if((ship->top_speed * ship->fuel) / ship->economy >= case_->distance)
				case_->successful++;
			
		}
		printf("%d\n", case_->successful);
	}
	
	return 0;
}
