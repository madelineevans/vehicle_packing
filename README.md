I created a search algorithm that will allow people to find locations to store multiple vehicles. The endpoint is (https://neighbor-two.vercel.app/) and accepts requests like: ```bash
    curl -X POST "http://your-api.com/" \
        -H "Content-Type: application/json" \
        -d '[
                {
                    "length": 10,
                    "quantity": 1
                },
                {
                    "length": 20,
                    "quantity": 2
                },
                {
                    "length": 25,
                    "quantity": 1
                }
            ]'
    ```
    where the width of each vehicle is assumed to be 10 feet. I search a set document of listings I have and return the cheapest result per location id for every possible location that could store 
    all the requested vehicles. It's returned in order of total price, ascending. I'm also assuming that at each location vehicles are stored at the same orientation and require no buffer space.
