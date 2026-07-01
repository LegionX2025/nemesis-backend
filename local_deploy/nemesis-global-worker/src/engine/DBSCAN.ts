export interface DBSCANPoint {
    id: string;
    features: number[];
}

export class DBSCAN {
    private epsilon: number;
    private minPts: number;

    constructor(epsilon: number, minPts: number) {
        this.epsilon = epsilon;
        this.minPts = minPts;
    }

    private euclideanDistance(p1: number[], p2: number[]): number {
        let sum = 0;
        for (let i = 0; i < Math.min(p1.length, p2.length); i++) {
            sum += Math.pow(p1[i] - p2[i], 2);
        }
        return Math.sqrt(sum);
    }

    private regionQuery(points: DBSCANPoint[], point: DBSCANPoint): DBSCANPoint[] {
        return points.filter(p => this.euclideanDistance(point.features, p.features) <= this.epsilon);
    }

    public cluster(points: DBSCANPoint[]): Map<string, number> {
        let clusterId = 0;
        const labels = new Map<string, number>(); // id -> clusterId (-1 means noise)
        const visited = new Set<string>();

        for (const point of points) {
            if (visited.has(point.id)) continue;
            visited.add(point.id);

            const neighbors = this.regionQuery(points, point);
            if (neighbors.length < this.minPts) {
                labels.set(point.id, -1); // Noise
            } else {
                clusterId++;
                this.expandCluster(point, neighbors, clusterId, points, visited, labels);
            }
        }

        return labels;
    }

    private expandCluster(
        point: DBSCANPoint, 
        neighbors: DBSCANPoint[], 
        clusterId: number, 
        points: DBSCANPoint[], 
        visited: Set<string>, 
        labels: Map<string, number>
    ) {
        labels.set(point.id, clusterId);

        let i = 0;
        while (i < neighbors.length) {
            const currentPoint = neighbors[i];
            
            if (!visited.has(currentPoint.id)) {
                visited.add(currentPoint.id);
                const currentNeighbors = this.regionQuery(points, currentPoint);
                if (currentNeighbors.length >= this.minPts) {
                    neighbors.push(...currentNeighbors);
                }
            }

            if (!labels.has(currentPoint.id) || labels.get(currentPoint.id) === -1) {
                labels.set(currentPoint.id, clusterId);
            }

            i++;
        }
    }
}
