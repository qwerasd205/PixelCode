class Animal {
    constructor (options) {
        this.type = options?.type ?? 'dog';
        this.adjectives = options?.adjectives;
    }

    get description () {
        return `${this.adjectives.join(' ')} ${this.type}`;
    }

    describe_action (verb, object) {
        return `${this.description} ${verb} ${object.description}.`;
    }
}

const adjective_prepender = adjective => animal => new Animal({
    type: animal.type,
    adjectives: [adjective].concat(animal.adjectives)
});

const The = adjective_prepender('The');
const the = adjective_prepender('the');

const quick_brown_fox = new Animal({ type: 'fox', adjectives: ['quick', 'brown'] });
const lazy_dog        = new Animal({ adjectives: ['lazy'] });

console.log(The(quick_brown_fox).describe_action('jumps over', the(lazy_dog)));
// "The quick brown fox jumps over the lazy dog."