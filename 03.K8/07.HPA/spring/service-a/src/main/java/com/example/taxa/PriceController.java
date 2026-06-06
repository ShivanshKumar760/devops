package com.example.taxa;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.RestTemplate;

import java.net.InetAddress;
import java.util.Map;

@RestController
public class PriceController {

    private final RestTemplate rest = new RestTemplate();
    private final String taxServiceUrl = System.getenv().getOrDefault(
            "TAX_SERVICE_URL",
            "http://service-java-b:8080"   // fallback for local testing ONLY
    );

        private final String helloMessage = System.getenv().getOrDefault(
            "HELLO_MESSAGE",
            "Hello"   // fallback for local testing ONLY
    );

    @GetMapping("/price")
    public Map<String, Object> price(@RequestParam double amount,
                                     @RequestParam String country) throws Exception {

        // Call Service B to get the tax for the given country
        // In a real application, you would want to handle errors and timeouts here
        // For simplicity, we assume the call always succeeds and returns a valid response
        // The expected response from Service B is a JSON object like:
        // {
        //   "tax": 5.0,
        //   "container": "service-b-container-name"
        // }
        //rest.getForObject() will automatically convert the JSON response into a Map
        // We then extract the "tax" value from the response and calculate the total price

        long sum = 0;
        for(long i = 0; i < 1_000_000_000L; i++) {
                sum += i;
        }

        System.out.println("Sum: " + sum);

        Map taxResponse = rest.getForObject(
                taxServiceUrl + "/tax?country=" + country,
                Map.class
        );

        double tax = Double.parseDouble(taxResponse.get("tax").toString());
        double total = amount + tax;

        String hostname = InetAddress.getLocalHost().getHostName();

        return Map.of(
                "service", "A",
                "amount", amount,
                "tax", tax,
                "total", total,
                "container", hostname,
                "service_b_container", taxResponse.get("container"),
                "hello_message", helloMessage
        );
    }
}
