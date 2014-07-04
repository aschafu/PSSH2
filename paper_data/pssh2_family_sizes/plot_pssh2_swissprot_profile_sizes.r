data <- read.table("~/pssh2_family_sizes/pssh2_swissprot_family_sizes_eval_equal_or_less_10e-10", header=TRUE)
sizes <- data$count
#mean, median:
print("Mean:")
mean(sizes)
print("Median:")
median(sizes)
#plot:
#png("~/pssh2_family_sizes/pssh2_swissprot_family_sizes_eval_equal_or_less_10e-10.png")
#hist(sizes, breaks=100, col="blue", xlab="profile size", main="Distribution of PSSH2 SwissProt profile sizes -\nnumber of PDB chains with E-value equal or less 10e-10")
#dev.off()
